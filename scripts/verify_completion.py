"""Independent CSV-level reconstruction and sample/measurement invariants."""
import csv
import hashlib
import json
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/occlusion_completion'


def read(path):
    with path.open() as f:return list(csv.DictReader(f))


def main():
    audit=json.loads((OUT/'measurement_audit.json').read_text())
    assert audit['passed']
    for source,expected in audit['source_hashes'].items():
        assert hashlib.sha256((ROOT/'results'/source).read_bytes()).hexdigest()==expected
    original={};meta={}
    for run in audit['runs']:
        conditions=read(ROOT/f'results/{run}/conditions.csv')
        metadata={r['condition_id']:r for r in conditions}
        assert len(metadata)==len(conditions)
        for model in ['aimv2','dinov2']:
            predictions=read(ROOT/f'results/{run}/{model}_predictions.csv')
            assert set(metadata)=={r['condition_id'] for r in predictions}
            for r in predictions:
                assert all(r[k]==v for k,v in metadata[r['condition_id']].items())
                assert int(r['correct'])==int(r['prediction']==r['label'])
                assert hashlib.sha256(bytes.fromhex(r['mask_hex'])).hexdigest()==r['mask_sha256']
                budget=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask_hex']),dtype=np.uint8)).mean()
                assert abs(budget-float(r['fraction']))<1e-12
                key=(run,r['condition_id'],model);assert key not in original
                original[key]=r
        meta.update({(run,k):v for k,v in metadata.items()})
    # Check nesting across saved budgets, including the original 25% run.
    nested=defaultdict(dict)
    for r in meta.values():
        if r['suite']=='standard' and r['pattern']!='clean' and r['fill']=='128':
            key=(r['cohort'],r['image_id'],r['pattern'],r['repeat'])
            nested[key][float(r['fraction'])]=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask_hex']),dtype=np.uint8)).astype(bool)
    nesting_checks=0
    for budgets in nested.values():
        ordered=sorted(budgets)
        for lower,upper in zip(ordered,ordered[1:]):
            assert not (budgets[lower]&~budgets[upper]).any()
            nesting_checks+=1
    # Reconstruct main image averages without pandas or the analysis functions.
    groups=defaultdict(list)
    for (run,cid,model),r in original.items():
        if r['suite']!='standard':continue
        key=(r['cohort'],r['image_id'],int(r['label']),int(r['fill']),float(r['fraction']),r['pattern'],model)
        groups[key].append(r)
    image_means={key:sum(float(r['correct']) for r in rows)/len(rows) for key,rows in groups.items()}
    foreground={key:sum(float(r['object_visibility']) for r in rows)/len(rows) for key,rows in groups.items()}
    checked=0
    for row in read(OUT/'accuracy_summary.csv'):
        c,f,fill,p=row['cohort'],float(row['fraction']),int(row['fill']),row['pattern']
        values={model:[v for k,v in image_means.items() if k[0]==c and k[3]==fill and k[4]==f and k[5]==p and k[6]==model] for model in ['aimv2','dinov2']}
        assert len(values['aimv2'])==len(values['dinov2'])==int(row['n_images'])
        a=sum(values['aimv2'])/len(values['aimv2']);b=sum(values['dinov2'])/len(values['dinov2'])
        expected={'aimv2':a,'dinov2':b,'aim_minus_dino':a-b}[row['metric']]
        assert abs(float(row['estimate'])-expected)<1e-10
        checked+=1
    checked_bins=0
    condition_groups=defaultdict(list)
    for (run,cid,model),r in original.items():
        if r['suite']=='standard' and r['pattern']!='clean':
            condition_groups[(r['cohort'],int(r['fill']),float(r['fraction']),r['pattern'],model)].append(r)
    for row in read(OUT/'foreground_bins.csv'):
        model=row['metric'];width=float(row['bin_width']);binid=int(row['fg_bin'])
        if row['convention']=='individual_repeats':
            key=(row['cohort'],int(row['fill']),float(row['fraction']),row['pattern'])
            selected={m:[r for r in condition_groups[key+(m,)] if min(int(float(r['object_visibility'])*round(1/width)),round(1/width)-1)==binid] for m in ['aimv2','dinov2']}
            n=len({r['image_id'] for r in selected['aimv2']});assert n==int(row['n_images'])
            if n<5:assert row['estimate']==''
            else:
                # Within a pattern every individual-repeat row has the same weight.
                a=sum(float(r['correct']) for r in selected['aimv2'])/len(selected['aimv2'])
                b=sum(float(r['correct']) for r in selected['dinov2'])/len(selected['dinov2'])
                assert abs(float(row['estimate'])-{'aimv2':a,'dinov2':b,'aim_minus_dino':a-b}[model])<1e-10
            checked_bins+=1
            continue
        keys=[k for k in image_means if k[0]==row['cohort'] and k[3]==int(row['fill']) and k[4]==float(row['fraction']) and k[5]==row['pattern'] and k[6]=='aimv2' and min(int(foreground[k]*round(1/width)),round(1/width)-1)==binid]
        assert len(keys)==int(row['n_images'])
        if len(keys)<5:assert row['estimate']==''
        else:
            a=sum(image_means[k] for k in keys)/len(keys)
            b=sum(image_means[k[:-1]+('dinov2',)] for k in keys)/len(keys)
            expected={'aimv2':a,'dinov2':b,'aim_minus_dino':a-b}[model]
            assert abs(float(row['estimate'])-expected)<1e-10
        checked_bins+=1
    checked_head=checked_regions=0
    if 'completion_head' in audit['runs']:
        def measurement(key,field):
            values=[float(r[field]) for r in groups[key] if r[field]!='']
            return sum(values)/len(values) if values else None
        for row in read(OUT/'standard_region_visibility.csv'):
            keys=[k for k in image_means if k[0]=='new_head' and k[3]==int(row['fill'])
                  and k[4]==float(row['fraction']) and k[5]==row['pattern'] and k[6]=='aimv2']
            for field in ['object_visibility','background_visibility','head_visibility','body_visibility','head_foreground_fraction']:
                values=[measurement(k,field) for k in keys]
                values=[v for v in values if v is not None]
                assert len(values)==int(row[field+'_n_images'])
                assert abs(sum(values)/len(values)-float(row[field]))<1e-10
                checked_regions+=1
        for row in read(OUT/'head_thirds.csv'):
            width=float(row['bin_width'])
            keys=[k for k in image_means if k[0]=='new_head' and k[3]==int(row['fill'])
                  and k[4]==float(row['fraction']) and k[5]==row['pattern'] and k[6]=='aimv2'
                  and min(int(foreground[k]*round(1/width)),round(1/width)-1)==int(row['fg_bin'])
                  and min(int(measurement(k,'head_visibility')*3),2)==int(row['head_third'])]
            assert len(keys)==int(row['n_images'])
            if len(keys)<5:assert row['estimate']==''
            else:
                a=sum(image_means[k] for k in keys)/len(keys)
                b=sum(image_means[k[:-1]+('dinov2',)] for k in keys)/len(keys)
                assert abs(float(row['estimate'])-{'aimv2':a,'dinov2':b,'aim_minus_dino':a-b}[row['metric']])<1e-10
            checked_head+=1
    previous=sum([json.loads((ROOT/f'results/{run}/manifest.json').read_text()) for run in ['pilot_v1','extension_v2']],[])
    newpath=ROOT/'results/completion_head/manifest.json'
    new_audit=None
    if newpath.exists():
        new=json.loads(newpath.read_text())
        assert len(new)==185 and Counter(r['label'] for r in new)==Counter({i:5 for i in range(37)})
        assert not ({r['image_id'] for r in new}&{r['image_id'] for r in previous})
        assert not ({r['image_sha256'] for r in new}&{r['image_sha256'] for r in previous})
        assert len({r['image_sha256'] for r in new})==185
        for r in new:
            assert hashlib.sha256((ROOT/f'data/raw/annotations/xmls/{r["image_id"]}.xml').read_bytes()).hexdigest()==r['xml_sha256']
        new_audit=dict(images=185,per_breed=5,prior_ids_and_bytes_disjoint=True,head_xml_hashes_verified=True)
    for run in ['completion_primary','completion_head']:
        path=ROOT/f'results/{run}'
        if not (path/'pre_inference_lock.json').exists():continue
        lock=json.loads((path/'pre_inference_lock.json').read_text())
        assert all(hashlib.sha256((path/name).read_bytes()).hexdigest()==h for name,h in lock.items())
        cfg=json.loads((path/'config.json').read_text())
        assert hashlib.sha256((ROOT/'docs/OCCLUSION_COMPLETION_PROTOCOL.md').read_bytes()).hexdigest()==cfg['protocol_sha256']
        if run in audit['runs']:
            for model in ['aimv2','dinov2']:
                features=np.load(path/f'features/{model}.npy',mmap_mode='r')
                assert np.isfinite(features).all()
                assert np.allclose(np.linalg.norm(features,axis=1),1.,atol=1e-5,rtol=0)
                replay=json.loads((path/f'{model}_replay.json').read_text())
                assert replay['passed'] and replay['classes_identical']
    result=dict(passed=True,included_runs=audit['runs'],source_conditions_verified=len(meta),
                independently_reconstructed_summary_cells=checked,independently_reconstructed_foreground_cells=checked_bins,
                saved_budget_nesting_checks=nesting_checks,
                independently_reconstructed_head_cells=checked_head,region_measurements_verified=checked_regions,
                mask_budgets_and_hashes_verified=True,new_head_sample=new_audit,
                scope='Point estimates and data/identity invariants independently reconstructed; bootstrap code separately unit-tested.')
    (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
