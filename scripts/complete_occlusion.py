"""Versioned budget extension and unused annotated cohort; frozen model inference."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import features

import extension_v2 as ext
from occlusion_visibility.data import load_image, read_split, sha256_file
from occlusion_visibility.encoders import FrozenEncoder
from occlusion_visibility.experiment import decode_mask, mask_hex
from occlusion_visibility.masks import apply_mask, coverage, stable_seed, visibility_mask

ROOT = Path(__file__).resolve().parents[1]
MODELS = ['aimv2', 'dinov2']
PROTOCOL = ROOT / 'docs/OCCLUSION_COMPLETION_PROTOCOL.md'


def config_for(cohort):
    return dict(run_name='completion_' + cohort, source_run='extension_v2',
                seed=6692031, size=224, patch=14, fills=[128, 0], random_seeds=[0, 1, 2],
                fractions=[.5, .75] if cohort == 'primary' else [.25, .5, .75],
                pair_caliper=.03, minimum_center_distance_patches=4,
                head_minimum_visibility_gap=.20, batch_size=8, device='mps', dtype='float32',
                completion_runner_sha256=sha256_file(Path(__file__)),
                protocol_sha256=sha256_file(PROTOCOL))


def choose_head():
    old = sum([json.loads((ROOT / f'results/{run}/manifest.json').read_text())
               for run in ['pilot_v1', 'extension_v2']], [])
    blocked_ids = {r['image_id'] for r in old}
    blocked_bytes = {r['image_sha256'] for r in old}
    pool, excluded = [], []
    for r in sorted(read_split(ROOT / 'data/raw/annotations/trainval.txt'), key=lambda r:r['image_id']):
        name = r['image_id']
        if name in blocked_ids:
            excluded.append(dict(image_id=name, reason='previously used ID')); continue
        digest = sha256_file(ROOT / f'data/raw/images/{name}.jpg')
        if digest in blocked_bytes:
            excluded.append(dict(image_id=name, reason='previously used or duplicate bytes')); continue
        try:
            _, trimap = load_image(ROOT, name)
            assert np.isin(trimap, [1, 2, 3]).all() and (trimap == 1).any()
            _, info = ext.load_head(ROOT, name, trimap)
        except (FileNotFoundError, ValueError, AssertionError, ext.ET.ParseError) as e:
            excluded.append(dict(image_id=name, reason=type(e).__name__)); continue
        blocked_bytes.add(digest)
        pool.append(dict(r, cohort='new_head', official_split='trainval', image_sha256=digest,
                         annotation_sha256=sha256_file(ROOT / f'data/raw/annotations/trimaps/{name}.png'), **info))
    chosen = ext.choose_balanced(pool, 5, np.random.default_rng(6692031))
    assert not ({r['image_id'] for r in chosen} & blocked_ids)
    return chosen, excluded, {str(i):sum(r['label']==i for r in pool) for i in range(37)}


def conditions(manifest, cfg):
    rows, inputs, eligible = [], [], []
    for r in manifest:
        name=r['image_id']; rgb, trimap = load_image(ROOT, name)
        inputs.append(dict(image_id=name, rgb_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),
                           trimap_sha256=hashlib.sha256(trimap.tobytes()).hexdigest()))
        head = ext.load_head(ROOT, name, trimap)[0] if r['cohort']=='new_head' else None
        entries=[]
        if head is not None: entries.append(('standard','clean',1.,0,'','',visibility_mask('clean',1.)))
        for fraction in cfg['fractions']:
            for pattern in ['prefix','suffix','center','random']:
                for repeat in ([0,1,2] if pattern=='random' else [0]):
                    mask=visibility_mask(pattern,fraction,seed=stable_seed(6692026,name,repeat))
                    assert mask.mean()==fraction
                    # The deterministic ordering must nest all visibility budgets.
                    lower=visibility_mask(pattern,.25,seed=stable_seed(6692026,name,repeat))
                    assert not (lower & ~mask).any()
                    entries.append(('standard',pattern,fraction,repeat,'','',mask))
        if head is not None:
            pairs=ext.head_pair(trimap,head,cfg)
            eligible.append(dict(image_id=name,cohort='new_head',eligible=bool(pairs)))
            for role,(pattern,mask,_,_,_) in pairs:
                entries.append(('paired',pattern,.75,0,'head_contrast',role,mask))
        for suite,pattern,fraction,repeat,pair_type,role,mask in entries:
            measurement={k:(v if np.isfinite(v) else None) for k,v in coverage(trimap,mask).items()}
            if head is not None:
                body=(trimap==1)&~head
                measurement.update(head_visibility=float(mask[head].mean()),
                                   body_visibility=float(mask[body].mean()) if body.any() else None,
                                   head_foreground_fraction=float(head.sum()/(trimap==1).sum()))
            code=mask_hex(mask,14)
            for fill in ([-1] if pattern=='clean' else cfg['fills']):
                row=dict(image_id=name,label=r['label'],cohort=r['cohort'],suite=suite,pattern=pattern,
                         fraction=fraction,repeat=repeat,pair_type=pair_type,pair_role=role,fill=fill,
                         mask_hex=code,mask_sha256=hashlib.sha256(bytes.fromhex(code)).hexdigest(),**measurement)
                row['condition_id']=hashlib.sha256(json.dumps([name,suite,pattern,fraction,repeat,pair_type,role,fill,code]).encode()).hexdigest()
                rows.append(row)
    assert len({r['condition_id'] for r in rows})==len(rows)
    return rows,inputs,eligible


def prepare(cohort):
    assert features.version_codec('jpg')=='9.0' and features.version_feature('libjpeg_turbo') is None
    cfg=config_for(cohort); out=ROOT/'results'/cfg['run_name']; out.mkdir(exist_ok=True)
    ext.write_json(out/'config.json',cfg)
    if cohort=='primary':
        manifest=[r for r in json.loads((ROOT/'results/extension_v2/manifest.json').read_text()) if r['cohort']=='primary']
        excluded=[]; pools={}
    else: manifest,excluded,pools=choose_head()
    rows,inputs,eligible=conditions(manifest,cfg)
    ext.write_json(out/'manifest.json',manifest)
    ext.write_json(out/'exclusions.json',excluded)
    ext.write_csv(out/'conditions.csv',rows); ext.write_csv(out/'preprocessing_fingerprints.csv',inputs)
    if eligible: ext.write_csv(out/'eligibility.csv',eligible)
    (out/'probes').mkdir(exist_ok=True); probes={}
    for model in MODELS:
        original=ROOT/f'results/extension_v2/probes/{model}_linear.npz'; dest=out/'probes'/original.name
        if not dest.exists():shutil.copyfile(original,dest)
        assert sha256_file(dest)==sha256_file(original)
        probes[model]={'sha256':sha256_file(dest),'C':10}
    if cohort=='primary':
        previous={r['image_id']:r for r in csv.DictReader((ROOT/'results/extension_v2/preprocessing_fingerprints.csv').open())}
        assert all(r==previous[r['image_id']] for r in inputs)
    audit=dict(images=len(manifest),rows_per_model=len(rows),frozen_probes=probes,
               eligible_head_pairs=sum(r['eligible'] for r in eligible),candidate_pool_by_breed=pools,
               distinct_image_hashes=len({r['image_sha256'] for r in manifest}),
               previous_manifest_sha256={run:sha256_file(ROOT/f'results/{run}/manifest.json') for run in ['pilot_v1','extension_v2']})
    ext.write_json(out/'preparation_audit.json',audit)
    ext.write_json(out/'pre_inference_lock.json',{p:sha256_file(out/p) for p in ['config.json','manifest.json','conditions.csv','preprocessing_fingerprints.csv','preparation_audit.json']})
    print(json.dumps(audit,indent=2),flush=True)


def verify_lock(out,cfg):
    assert config_for(cfg['run_name'].removeprefix('completion_'))==cfg,'Runner/protocol changed after design lock'
    lock=json.loads((out/'pre_inference_lock.json').read_text())
    assert all(sha256_file(out/p)==digest for p,digest in lock.items())


def replay(model,out,cfg):
    import gc,torch
    original=ROOT/'results/extension_v2'
    rows=list(csv.DictReader((original/'conditions.csv').open()))[:8]
    encoder=FrozenEncoder(ROOT,model,'mps')
    pixels=np.stack([apply_mask(load_image(ROOT,r['image_id'])[0],decode_mask(r['mask_hex'],224,14),max(0,int(r['fill']))) for r in rows])
    actual=encoder.encode(pixels)
    expected=np.load(original/f'features/{model}.npy',mmap_mode='r')[:8]
    with np.load(out/f'probes/{model}_linear.npz') as head:
        a,_=ext.predict(actual,head);b,_=ext.predict(expected,head)
    result=dict(model=model,conditions=8,max_absolute_feature_difference=float(np.abs(actual-expected).max()),
                classes_identical=bool(np.array_equal(a,b)),torch_version=torch.__version__,
                benchmark=encoder.benchmark(8))
    result['passed']=bool(np.allclose(actual,expected,atol=1e-5,rtol=0) and result['classes_identical'])
    ext.write_json(out/f'{model}_replay.json',result)
    print(json.dumps(result),flush=True)
    assert result['passed'],'Replay failed; no new inference allowed'
    del encoder;gc.collect();torch.mps.empty_cache()


def audit(out,cfg):
    verify_lock(out,cfg)
    manifest=json.loads((out/'manifest.json').read_text())
    ext.verify_inputs(ROOT,out,manifest)
    regenerated,_,_=conditions(manifest,cfg)
    original=list(csv.DictReader((out/'conditions.csv').open()))
    assert len(regenerated)==len(original)
    for a,b in zip(regenerated,original):
        for k,v in a.items():assert ('' if v is None else str(v))==b[k],(k,v,b[k])
    models=[]
    for model in MODELS:
        predictions=list(csv.DictReader((out/f'{model}_predictions.csv').open()))
        assert len(predictions)==len(original)
        for r,p in zip(original,predictions):
            assert all(r[k]==p[k] for k in r)
            assert int(p['correct'])==int(int(p['prediction'])==int(p['label']))
        binding=ext.cache_binding(ROOT,out,cfg,original,model)
        assert json.loads((out/f'features/{model}.json').read_text())==binding
        matrix=np.load(out/f'features/{model}.npy',mmap_mode='r')
        assert np.isfinite(matrix).all()
        with np.load(out/f'probes/{model}_linear.npz') as head:labels,probs=ext.predict(matrix,head)
        assert np.array_equal(labels,[int(r['prediction']) for r in predictions])
        assert np.allclose(probs[np.arange(len(labels)),[int(r['label']) for r in original]],
                           [float(r['target_probability']) for r in predictions],atol=1e-12,rtol=0)
        models.append(model)
    result=dict(passed=True,images=len(manifest),conditions_per_model=len(original),
                completed_models=models,annotations_regenerated=True,predictions_reconstructed=True)
    (out/'integration_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','run','audit']);p.add_argument('--cohort',choices=['primary','head'],required=True);p.add_argument('--model',choices=MODELS)
    a=p.parse_args()
    if a.stage=='prepare':prepare(a.cohort)
    else:
        out=ROOT/f'results/completion_{a.cohort}';cfg=json.loads((out/'config.json').read_text());verify_lock(out,cfg)
        if a.stage=='audit':audit(out,cfg)
        else:
            assert a.model
            if not (out/f'{a.model}_replay.json').exists():replay(a.model,out,cfg)
            else:assert json.loads((out/f'{a.model}_replay.json').read_text())['passed']
            ext.run(ROOT,cfg,a.model)
