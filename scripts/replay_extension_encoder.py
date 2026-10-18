"""Replay a few aligned batches in an independent interpreter after the full run."""
import gc
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from PIL import features
from occlusion_visibility.data import load_image
from occlusion_visibility.encoders import FrozenEncoder
from occlusion_visibility.experiment import decode_mask
from occlusion_visibility.masks import apply_mask

root = Path(__file__).resolve().parents[1]
out = root / 'results/extension_v2'
config = json.loads((out / 'config.json').read_text())
audit = json.loads((out / 'integration_audit.json').read_text())
assert set(audit['completed_and_reconstructed_models']) == {'aimv2', 'dinov2'}
assert features.version_codec('jpg') == '9.0' and features.version_feature('libjpeg_turbo') is None
assert Path(sys.prefix).resolve() != (root / '.reference-conda').resolve(), 'Use a separate interpreter for this audit'
rows = pd.read_csv(out / 'conditions.csv', keep_default_na=False)
boundary = int(rows.index[rows.cohort == 'auxiliary_head'][0])
# All starts align to the original batch-size-8 inference schedule.
starts = [0, boundary // 8 * 8, boundary // 8 * 8 + 8]
result = {'scope': 'Three aligned batches per model (initial primary conditions and the primary/auxiliary boundary); not a second full experiment.',
          'python_executable': sys.executable, 'python_prefix': sys.prefix,
          'independent_from_reference_conda': True, 'torch_version': torch.__version__,
          'jpeg_api_version': features.version_codec('jpg'), 'batches_per_model': len(starts), 'models': []}
for name in ['aimv2', 'dinov2']:
    encoder = FrozenEncoder(root, name, config['device'])
    cached = np.load(out / 'features' / f'{name}.npy', mmap_mode='r')
    biggest, count = 0., 0
    all_match = True
    for start in starts:
        batch = rows.iloc[start:start + 8]
        pixels = []
        for r in batch.itertuples():
            rgb, _ = load_image(root, r.image_id)
            pixels.append(apply_mask(rgb, decode_mask(r.mask_hex, 224, 14), max(0, int(r.fill))))
        actual = encoder.encode(np.stack(pixels))
        expected = cached[start:start + len(batch)]
        biggest = max(biggest, float(np.abs(actual - expected).max()))
        all_match &= bool(np.allclose(actual, expected, atol=1e-5, rtol=0))
        count += len(batch)
    norms = np.linalg.norm(cached, axis=1)
    entry = {'model': name, 'replayed_conditions': count, 'max_abs_feature_difference': biggest,
             'matches_at_atol_1e_5_rtol_0': all_match, 'all_cached_feature_norms_near_one': bool(np.allclose(norms, 1, atol=1e-5, rtol=0)),
             'cached_norm_min': float(norms.min()), 'cached_norm_max': float(norms.max())}
    result['models'].append(entry)
    print(json.dumps(entry), flush=True)
    del encoder
    gc.collect()
    torch.mps.empty_cache()
result['passed'] = all(r['matches_at_atol_1e_5_rtol_0'] and r['all_cached_feature_norms_near_one'] for r in result['models'])
(root / 'docs/EXTENSION_ENCODER_REPLAY_CHECK.json').write_text(json.dumps(result, indent=2) + '\n')
assert result['passed'], 'Encoder replay mismatch; retain diagnostic evidence and investigate.'
