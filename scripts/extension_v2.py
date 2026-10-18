"""Versioned follow-up. Keep the pilot core and its cache bindings untouched."""
from __future__ import annotations
import argparse
import csv
import gc
import hashlib
import json
import shutil
import time
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, features as pil_features

from occlusion_visibility.data import load_image, read_split, sha256_file
from occlusion_visibility.encoders import FrozenEncoder
from occlusion_visibility.experiment import decode_mask, mask_hex
from occlusion_visibility.masks import apply_mask, candidate_square_masks, coverage, select_pairs, stable_seed, visibility_mask

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    data = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f'Refuse to change frozen input: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def rectangle_proxy(trimap, original_size, box):
    """PASCAL 1-based inclusive box -> resized pixel-center rectangle intersect FG."""
    width, height = original_size
    xmin, ymin, xmax, ymax = box
    if not (1 <= xmin <= xmax <= width and 1 <= ymin <= ymax <= height):
        raise ValueError('Invalid head box coordinates')
    h, w = trimap.shape
    x = (np.arange(w) + .5) * width / w
    y = (np.arange(h) + .5) * height / h
    rectangle = (y[:, None] >= ymin - 1) & (y[:, None] < ymax) & (x[None, :] >= xmin - 1) & (x[None, :] < xmax)
    return rectangle & (trimap == 1)


def load_head(root, image_id, trimap):
    xml = root / 'data/raw/annotations/xmls' / f'{image_id}.xml'
    tree = ET.parse(xml).getroot()
    with Image.open(root / 'data/raw/images' / f'{image_id}.jpg') as image:
        dimensions = image.size
    xml_size = (int(tree.findtext('size/width')), int(tree.findtext('size/height')))
    if dimensions != xml_size:
        raise ValueError('XML/image dimension mismatch')
    boxes = tree.findall('object/bndbox')
    if len(boxes) != 1:
        raise ValueError('Expected one annotated head box')
    box = [int(boxes[0].findtext(k)) for k in ['xmin', 'ymin', 'xmax', 'ymax']]
    head = rectangle_proxy(trimap, dimensions, box)
    if not head.any():
        raise ValueError('No foreground inside head box after resize')
    return head, {'xml_sha256': sha256_file(xml), 'original_size': list(dimensions), 'head_box_pascal': box}


def head_pair(trimap, head, config):
    candidates = [(n, m, p, float(m[trimap == 1].mean()), float(m[head].mean()))
                  for n, m, p in candidate_square_masks()]
    choices = []
    for i, a in enumerate(candidates):
        for b in candidates[i + 1:]:
            gap = abs(a[3] - b[3])
            distance = float(np.linalg.norm(np.asarray(a[2]) - np.asarray(b[2])))
            head_gap = abs(a[4] - b[4])
            if gap <= config['pair_caliper'] and distance >= config['minimum_center_distance_patches'] and head_gap >= config['head_minimum_visibility_gap']:
                choices.append((head_gap, -gap, distance, a[0], b[0], a, b))
    if not choices:
        return []
    winner = max(choices, key=lambda p: p[:5])
    a, b = sorted(winner[-2:], key=lambda r: (r[4], r[0]), reverse=True)
    return [('high', a), ('low', b)]


def choose_balanced(candidates, per_class, rng):
    result = []
    for label in range(37):
        group = sorted([r for r in candidates if r['label'] == label], key=lambda r: r['image_id'])
        if len(group) < per_class:
            raise ValueError(f'Insufficient class {label}: {len(group)} < {per_class}')
        indices = rng.permutation(len(group))[:per_class]
        result.extend(group[int(i)] for i in indices)
    return result


def sample_inputs(root, config):
    prior = json.loads((root / 'results' / config['source_run'] / 'manifest.json').read_text())
    blocked_ids = {r['image_id'] for r in prior}
    blocked_hashes = {r['image_sha256'] for r in prior}
    seen_hashes = set(blocked_hashes)
    excluded, pools = [], {'primary': [], 'auxiliary_head': []}
    for cohort, file in [('primary', 'test.txt'), ('auxiliary_head', 'trainval.txt')]:
        for row in sorted(read_split(root / 'data/raw/annotations' / file), key=lambda r: r['image_id']):
            image_id = row['image_id']
            reason = None
            if image_id in blocked_ids:
                reason = 'Previously used pilot ID'
            digest = sha256_file(root / 'data/raw/images' / f'{image_id}.jpg')
            if reason is None and digest in seen_hashes:
                reason = 'Previously used or duplicate image bytes'
            head_info = {}
            if reason is None:
                _, trimap = load_image(root, image_id)
                if not np.isin(trimap, [1, 2, 3]).all() or not (trimap == 1).any():
                    reason = 'Invalid or empty foreground after resize'
                elif cohort == 'auxiliary_head':
                    try:
                        _, head_info = load_head(root, image_id, trimap)
                    except (FileNotFoundError, ValueError, ET.ParseError) as error:
                        reason = f'Invalid/missing head annotation: {error.__class__.__name__}'
            if reason is not None:
                excluded.append(dict(row, cohort=cohort, reason=reason))
                continue
            seen_hashes.add(digest)
            pools[cohort].append(dict(row, cohort=cohort, image_sha256=digest,
                annotation_sha256=sha256_file(root / 'data/raw/annotations/trimaps' / f'{image_id}.png'), **head_info))
    rng = np.random.default_rng(config['seed'])
    main = choose_balanced(pools['primary'], config['primary_test_per_class'], rng)
    auxiliary = choose_balanced(pools['auxiliary_head'], config['auxiliary_head_per_class'], rng)
    return main + auxiliary, excluded, {k: len(v) for k, v in pools.items()}


def make_conditions(root, manifest, config):
    rows, eligibility, inputs = [], [], []
    for sample in manifest:
        image_id = sample['image_id']
        rgb, trimap = load_image(root, image_id)
        inputs.append({'image_id': image_id, 'rgb_sha256': hashlib.sha256(rgb.tobytes()).hexdigest(),
                       'trimap_sha256': hashlib.sha256(trimap.tobytes()).hexdigest()})
        entries = [('standard', 'clean', 1., 0, '', '', visibility_mask('clean', 1.))]
        head = None
        if sample['cohort'] == 'primary':
            for pattern in ['prefix', 'suffix', 'center', 'random']:
                for repeat in (config['random_seeds'] if pattern == 'random' else [0]):
                    mask = visibility_mask(pattern, config['primary_fraction'], seed=stable_seed(6692026, image_id, repeat))
                    entries.append(('standard', pattern, config['primary_fraction'], repeat, '', '', mask))
            pairs = select_pairs(trimap, caliper=config['pair_caliper'])
            eligibility.append({'image_id': image_id, 'cohort': 'primary',
                                'eligible': any(p[0] == 'visibility_matched' for p in pairs)})
            for pair_type, role, (name, mask, _, _) in pairs:
                entries.append(('paired', name, float(mask.mean()), 0, pair_type, role, mask))
        else:
            head, _ = load_head(root, image_id, trimap)
            pairs = head_pair(trimap, head, config)
            eligibility.append({'image_id': image_id, 'cohort': 'auxiliary_head', 'eligible': bool(pairs)})
            for role, (name, mask, _, _, _) in pairs:
                entries.append(('paired', name, float(mask.mean()), 0, 'head_contrast', role, mask))
        for suite, pattern, fraction, repeat, pair_type, role, mask in entries:
            code = mask_hex(mask, config['patch'])
            measurement = {k: (v if np.isfinite(v) else None) for k, v in coverage(trimap, mask).items()}
            if head is not None:
                body = (trimap == 1) & ~head
                measurement.update(head_visibility=float(mask[head].mean()),
                    body_visibility=float(mask[body].mean()) if body.any() else None,
                    head_foreground_fraction=float(head.sum() / (trimap == 1).sum()))
            for fill in ([-1] if pattern == 'clean' else config['fills']):
                row = dict(image_id=image_id, label=sample['label'], cohort=sample['cohort'], suite=suite,
                    pattern=pattern, fraction=fraction, repeat=repeat, pair_type=pair_type, pair_role=role,
                    fill=fill, mask_hex=code, mask_sha256=hashlib.sha256(bytes.fromhex(code)).hexdigest(), **measurement)
                row['condition_id'] = hashlib.sha256(json.dumps([image_id, suite, pattern, repeat, pair_type, role, fill]).encode()).hexdigest()
                rows.append(row)
    return rows, eligibility, inputs


def verify_inputs(root, out, manifest):
    expected = {r['image_id']: r for r in csv.DictReader((out / 'preprocessing_fingerprints.csv').open())}
    for sample in manifest:
        image_id = sample['image_id']
        assert sha256_file(root / 'data/raw/images' / f'{image_id}.jpg') == sample['image_sha256']
        assert sha256_file(root / 'data/raw/annotations/trimaps' / f'{image_id}.png') == sample['annotation_sha256']
        rgb, trimap = load_image(root, image_id)
        assert hashlib.sha256(rgb.tobytes()).hexdigest() == expected[image_id]['rgb_sha256'], image_id
        assert hashlib.sha256(trimap.tobytes()).hexdigest() == expected[image_id]['trimap_sha256'], image_id
    return len(manifest)


def prepare(root, config):
    assert pil_features.version_codec('jpg') == '9.0' and pil_features.version_feature('libjpeg_turbo') is None
    out = root / 'results' / config['run_name']
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'config.json', config)
    manifest, exclusions, pools = sample_inputs(root, config)
    rows, eligible, inputs = make_conditions(root, manifest, config)
    write_json(out / 'manifest.json', manifest)
    write_json(out / 'exclusions.json', exclusions)
    write_csv(out / 'conditions.csv', rows)
    write_csv(out / 'eligibility.csv', eligible)
    write_csv(out / 'preprocessing_fingerprints.csv', inputs)
    probes = out / 'probes'
    probes.mkdir(exist_ok=True)
    probe_info = {}
    for name in ['aimv2', 'dinov2']:
        selection = root / 'results' / config['source_run'] / f'{name}_probe.json'
        assert json.loads(selection.read_text())['chosen']['C'] == 10, 'Original selected C changed'
        source = root / 'results' / config['source_run'] / 'classifiers' / f'{name}_linear.npz'
        target = probes / source.name
        if not target.exists():
            shutil.copyfile(source, target)
        if source.exists():
            assert sha256_file(source) == sha256_file(target), 'Frozen source classifier changed'
        head = np.load(target)
        assert head['coef'].shape == (37, 1024) and np.array_equal(head['classes'], np.arange(37))
        probe_info[name] = {'sha256': sha256_file(target), 'C': 10, 'training': 'Original pilot clean train only; frozen for extension'}
    xml_ids = {p.stem for p in (root / 'data/raw/annotations/xmls').glob('*.xml')}
    official_test_ids = {r['image_id'] for r in read_split(root / 'data/raw/annotations/test.txt')}
    audit = {'new_images': len(manifest), 'primary_images': sum(r['cohort'] == 'primary' for r in manifest),
             'auxiliary_images': sum(r['cohort'] == 'auxiliary_head' for r in manifest), 'rows_per_model': len(rows),
             'candidate_pool_sizes': pools, 'official_test_head_xmls': len(xml_ids & official_test_ids),
             'eligibility': {c: {'eligible': sum(r['eligible'] for r in eligible if r['cohort'] == c),
                                 'total': sum(r['cohort'] == c for r in eligible)} for c in pools}, 'frozen_probes': probe_info}
    write_json(out / 'preparation_audit.json', audit)
    print(json.dumps(audit, indent=2), flush=True)


def cache_binding(root, out, config, rows, name):
    core = hashlib.sha256()
    for path in sorted((root / 'src/occlusion_visibility').glob('*.py')):
        core.update(path.read_bytes())
    source = json.loads((root / 'docs/SOURCES.json').read_text())
    for folder, key in [('ml-aim', 'aim_code'), ('dinov2', 'dino_code')]:
        import subprocess
        assert subprocess.check_output(['git', '-C', str(root / 'vendor' / folder), 'rev-parse', 'HEAD'], text=True).strip() == source[key]['revision']
        assert not subprocess.check_output(['git', '-C', str(root / 'vendor' / folder), 'diff', '--name-only'], text=True).strip()
    weight = root / 'models' / ('aimv2-large-patch14-224.safetensors' if name == 'aimv2' else 'dinov2_vitl14_pretrain.pth')
    weight_sha = sha256_file(weight)
    assert weight_sha == source['aim_weights' if name == 'aimv2' else 'dino_weights']['sha256']
    probe_sha = sha256_file(out / 'probes' / f'{name}_linear.npz')
    assert probe_sha == json.loads((out / 'preparation_audit.json').read_text())['frozen_probes'][name]['sha256']
    return {'config': config, 'conditions_sha256': sha256_file(out / 'conditions.csv'),
            'decoded_inputs_sha256': sha256_file(out / 'preprocessing_fingerprints.csv'),
            'core_source_sha256': core.hexdigest(), 'runner_sha256': sha256_file(Path(__file__)),
            'checkpoint_sha256': weight_sha, 'probe_sha256': probe_sha,
            'shape': [len(rows), 1024], 'dtype': 'float32'}


def predict(features, head):
    logits = features @ head['coef'].T + head['intercept']
    probability = np.exp(logits - logits.max(axis=1, keepdims=True))
    probability /= probability.sum(axis=1, keepdims=True)
    return head['classes'][probability.argmax(axis=1)], probability


def run(root, config, name):
    out = root / 'results' / config['run_name']
    assert json.loads((out / 'config.json').read_text()) == config
    manifest = json.loads((out / 'manifest.json').read_text())
    print('Verified decoded inputs', verify_inputs(root, out, manifest), flush=True)
    rows = list(csv.DictReader((out / 'conditions.csv').open()))
    binding = cache_binding(root, out, config, rows, name)
    directory = out / 'features'
    directory.mkdir(exist_ok=True)
    meta = directory / f'{name}.json'
    path = directory / f'{name}.npy'
    if meta.exists():
        assert json.loads(meta.read_text()) == binding, 'Stale cache binding; choose a new run'
        matrix = np.lib.format.open_memmap(path, mode='r+')
    else:
        matrix = np.lib.format.open_memmap(path, mode='w+', dtype='float32', shape=(len(rows), 1024))
        matrix[:] = np.nan
        matrix.flush()
        write_json(meta, binding)
    missing = np.flatnonzero(~np.isfinite(matrix).all(axis=1))
    if len(missing):
        encoder = FrozenEncoder(root, name, config['device'])
        print('benchmark', name, encoder.benchmark(config['batch_size']), flush=True)
        @lru_cache(maxsize=64)
        def rgb(image_id):
            return load_image(root, image_id)[0]
        started = time.monotonic()
        for start in range(0, len(missing), config['batch_size']):
            indices = missing[start:start + config['batch_size']]
            pixels = [apply_mask(rgb(rows[i]['image_id']), decode_mask(rows[i]['mask_hex'], 224, 14), max(0, int(rows[i]['fill']))) for i in indices]
            value = encoder.encode(np.stack(pixels))
            assert value.shape == (len(indices), 1024) and np.isfinite(value).all()
            matrix[indices] = value
            matrix.flush()
            if start == 0 or start // config['batch_size'] % 50 == 0 or start + len(indices) == len(missing):
                done = start + len(indices)
                print(f'{name}: {done}/{len(missing)} new conditions ({done/max(time.monotonic()-started,.001):.1f} img/s)', flush=True)
        del encoder
        gc.collect()
        import torch
        if config['device'] == 'mps':
            torch.mps.empty_cache()
    with np.load(out / 'probes' / f'{name}_linear.npz') as head:
        labels, probabilities = predict(np.asarray(matrix), head)
    for i, row in enumerate(rows):
        row.update(model=name, prediction=int(labels[i]), correct=int(labels[i] == int(row['label'])),
                   target_probability=float(probabilities[i, int(row['label'])]))
    write_csv(out / f'{name}_predictions.csv', rows)
    print('Saved complete predictions', name, len(rows), flush=True)


def audit(root, config, require_predictions=False):
    out = root / 'results' / config['run_name']
    manifest = json.loads((out / 'manifest.json').read_text())
    prior = json.loads((root / 'results' / config['source_run'] / 'manifest.json').read_text())
    assert not ({r['image_id'] for r in manifest} & {r['image_id'] for r in prior})
    assert not ({r['image_sha256'] for r in manifest} & {r['image_sha256'] for r in prior})
    assert len({r['image_sha256'] for r in manifest}) == len(manifest)
    assert len({r['image_id'] for r in manifest}) == len(manifest)
    for cohort, amount in [('primary', config['primary_test_per_class']), ('auxiliary_head', config['auxiliary_head_per_class'])]:
        assert [sum(r['cohort'] == cohort and r['label'] == label for r in manifest) for label in range(37)] == [amount] * 37
    verify_inputs(root, out, manifest)
    regenerated, eligibility, _ = make_conditions(root, manifest, config)
    original = list(csv.DictReader((out / 'conditions.csv').open()))
    assert len(regenerated) == len(original)
    for a, b in zip(regenerated, original):
        for key, value in a.items():
            if value is None:
                assert b[key] == ''
            elif isinstance(value, float):
                assert abs(value - float(b[key])) < 1e-12, (key, value, b[key])
            else:
                assert str(value) == b[key], key
    completed = []
    for name in ['aimv2', 'dinov2']:
        path = out / f'{name}_predictions.csv'
        if not path.exists():
            assert not require_predictions, f'Missing predictions: {name}'
            continue
        predictions = list(csv.DictReader(path.open()))
        assert len(predictions) == len(original)
        for a, b in zip(original, predictions):
            for key in a:
                assert a[key] == b[key], key
            assert int(b['correct']) == (int(b['label']) == int(b['prediction']))
        binding = cache_binding(root, out, config, original, name)
        assert json.loads((out / 'features' / f'{name}.json').read_text()) == binding
        matrix = np.load(out / 'features' / f'{name}.npy', mmap_mode='r')
        with np.load(out / 'probes' / f'{name}_linear.npz') as head:
            labels, probabilities = predict(matrix, head)
        assert np.array_equal(labels, [int(r['prediction']) for r in predictions])
        assert np.allclose(probabilities[np.arange(len(original)), [int(r['label']) for r in original]],
                           [float(r['target_probability']) for r in predictions], atol=1e-12)
        completed.append(name)
    result = {'passed': True, 'images': len(manifest), 'conditions_per_model': len(original),
              'new_ids_and_bytes_disjoint_from_all_pilot_samples': True, 'all_conditions_annotation_regenerated': True,
              'all_input_fingerprints_match': True, 'completed_and_reconstructed_models': completed,
              'eligibility': {cohort: {'eligible': sum(r['eligible'] for r in eligibility if r['cohort'] == cohort),
                                     'total': sum(r['cohort'] == cohort for r in eligibility)} for cohort in ['primary', 'auxiliary_head']}}
    (out / 'integration_audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('stage', choices=['prepare', 'run', 'audit'])
    p.add_argument('--model', choices=['aimv2', 'dinov2'])
    p.add_argument('--config', default='configs/extension_v2.json')
    p.add_argument('--require-predictions', action='store_true')
    args = p.parse_args()
    config = json.loads((ROOT / args.config).read_text())
    if args.stage == 'prepare':
        prepare(ROOT, config)
    elif args.stage == 'run':
        if not args.model:
            p.error('--model required')
        run(ROOT, config, args.model)
    else:
        audit(ROOT, config, args.require_predictions)


if __name__ == '__main__':
    main()
