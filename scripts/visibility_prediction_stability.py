"""Post-hoc fold-allocation sensitivity; preserve the original diagnostic run."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('visibility_prediction', ROOT / 'scripts/visibility_prediction.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
base = m.OUT
record = json.loads((base / 'design_record.json').read_text())
for seed in [6692029, 6692030]:
    m.OUT = base / f'fold_seed_{seed}'
    m.OUT.mkdir(exist_ok=False)
    m.SEED = seed
    m.PENALTIES = [1.0]
    sensitivity = dict(record)
    sensitivity['post_hoc_fold_sensitivity'] = {
        'fold_seed': seed, 'penalty': 1.0,
        'source_sha256': hashlib.sha256((ROOT / 'docs/VISIBILITY_PREDICTION_STABILITY.md').read_bytes()).hexdigest()}
    (m.OUT / 'design_record.json').write_text(json.dumps(sensitivity, indent=2) + '\n')
    m.run()
