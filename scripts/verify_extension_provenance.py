"""Check frozen follow-up artifacts and the auxiliary XML bytes against their sources."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/extension_v2'
REFERENCE_COMMIT = '815a33b'
FILES = ['configs/extension_v2.json', 'docs/EXTENSION_V2_PROTOCOL.md', 'docs/SOURCES.json',
         'scripts/extension_v2.py', 'scripts/analyze_extension.py']
FILES += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'src/occlusion_visibility').glob('*.py'))]
FILES += ['results/extension_v2/' + f for f in ['config.json', 'manifest.json', 'conditions.csv',
          'preprocessing_fingerprints.csv', 'preparation_audit.json', 'eligibility.csv', 'exclusions.json',
          'probes/aimv2_linear.npz', 'probes/dinov2_linear.npz']]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(record=False):
    inventory_path = OUT / 'frozen_provenance.json'
    if record and not inventory_path.exists():
        expected = {}
        for path in FILES:
            committed = subprocess.check_output(['git', 'show', REFERENCE_COMMIT + ':' + path], cwd=ROOT)
            assert (ROOT / path).read_bytes() == committed, f'Changed since pre-inference commit: {path}'
            expected[path] = sha(committed)
        inventory_path.write_text(json.dumps({'reference_commit': REFERENCE_COMMIT, 'frozen_file_sha256': expected}, indent=2) + '\n')
    inventory = json.loads(inventory_path.read_text())
    for path, digest in inventory['frozen_file_sha256'].items():
        assert sha((ROOT / path).read_bytes()) == digest, f'Frozen source changed: {path}'
    sources = json.loads((ROOT / 'docs/SOURCES.json').read_text())
    revisions = {}
    for folder, key in [('ml-aim', 'aim_code'), ('dinov2', 'dino_code')]:
        revision = subprocess.check_output(['git', '-C', str(ROOT / 'vendor' / folder), 'rev-parse', 'HEAD'], text=True).strip()
        assert revision == sources[key]['revision']
        assert not subprocess.check_output(['git', '-C', str(ROOT / 'vendor' / folder), 'diff', '--name-only'], text=True).strip()
        revisions[folder] = revision
    manifest = json.loads((OUT / 'manifest.json').read_text())
    xml_count = 0
    for row in manifest:
        if row['cohort'] == 'auxiliary_head':
            data = (ROOT / 'data/raw/annotations/xmls' / (row['image_id'] + '.xml')).read_bytes()
            assert sha(data) == row['xml_sha256'], row['image_id']
            xml_count += 1
    result = {'passed': True, 'reference_commit': inventory['reference_commit'],
              'frozen_file_count': len(inventory['frozen_file_sha256']),
              'all_frozen_files_unchanged': True, 'auxiliary_xml_files_verified': xml_count,
              'upstream_code_revisions': revisions,
              'scope': 'Source/input provenance check, not a second model experiment or proof of scientific validity.'}
    (OUT / 'provenance_audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--record', action='store_true', help='First record must match the pre-inference Git commit exactly.')
    check(parser.parse_args().record)
