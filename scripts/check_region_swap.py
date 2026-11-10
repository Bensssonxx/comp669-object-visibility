"""Independent review from published CSVs; pass --pixels with original data locally."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/region_swap'


def read(filename):
    with (OUT/filename).open() as file:
        return list(csv.DictReader(file))


def check(raw=False):
    for path,value in json.loads((OUT/'design_lock.json').read_text()).items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==value
    pool=read('candidates.csv')
    assert len({r['image_id'] for r in pool})==len(pool)
    good=[r for r in pool if r['reason']=='valid']
    historical=[r for run in ['pilot_v1','extension_v2','completion_head','completion_primary']
                for r in json.loads((ROOT/'results'/run/'manifest.json').read_text())]
    ids={r['image_id'] for r in good}
    hashes={r['jpeg_sha256'] for r in good}
    assert len(ids)==len(hashes)
    assert ids.isdisjoint(r['image_id'] for r in historical)
    assert hashes.isdisjoint(r['image_sha256'] for r in historical)
    direct={r['image_id'] for r in good if r['direct_eligible']=='True'}
    regional={r['image_id'] for r in good if r['regional']=='True'}
    assert len([r for r in good if r['direct']=='True'])==370
    for label in range(37):
        members=[r for r in good if int(r['label'])==label]
        assert len([r for r in members if r['regional']=='True'])==min(10,sum(r['regional_eligible']=='True' for r in members))
    by_name=defaultdict(dict)
    for r in read('conditions.csv'):
        assert r['condition'] not in by_name[r['image_id']]
        by_name[r['image_id']][r['condition']]=r
    assert set(by_name)==direct|regional
    if raw:
        import numpy as np
        from occlusion_visibility.data import load_image, read_split, sha256_file
        official={r['image_id']:r['label'] for r in read_split(ROOT/'data/raw/annotations/test.txt')}
        for r in good:
            assert official[r['image_id']]==int(r['label'])
            assert sha256_file(ROOT/'data/raw/images'/(r['image_id']+'.jpg'))==r['jpeg_sha256']
        from occlusion_visibility.masks import apply_mask
    for name,group in by_name.items():
        required={'center'}
        if name in direct: required.update(['relocated1','relocated2'])
        if name in regional: required.update(['animal','background','both'])
        assert set(group)==required
        bit={k:int(r['mask_hex'],16) for k,r in group.items()}
        assert all(v.bit_count()==64 for v in bit.values())
        if name in regional:
            fg=bit['center']^bit['animal']
            bg=bit['center']^bit['background']
            assert fg.bit_count()==bg.bit_count()==8 and not fg&bg
            assert (bit['center']^fg^bg)==bit['both']
            assert len({(group[c]['animal_pixels'],group[c]['background_pixels']) for c in ['center','animal','background','both']})==1
        if raw:
            rgb,trimap=load_image(ROOT,name)
            masks={}
            for c,r in group.items():
                grid=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask_hex']),dtype=np.uint8))
                mask=grid.reshape(16,16).repeat(14,0).repeat(14,1).astype(bool)
                masks[c]=mask
                assert hashlib.sha256(apply_mask(rgb,mask,128).tobytes()).hexdigest()==r['input_sha256']
                assert hashlib.sha256(trimap.tobytes()).hexdigest()==r['trimap_sha256']
                assert (mask & (trimap==1)).sum()==int(r['animal_pixels'])
                assert (mask & (trimap==2)).sum()==int(r['background_pixels'])
            if name in regional:
                for c,target in [('animal',1),('background',2)]:
                    assert np.all(trimap[masks[c]^masks['center']]==target)
            if name in direct:
                for c in ['relocated1','relocated2']:
                    assert abs(float(masks[c][trimap==1].mean()-masks['center'][trimap==1].mean()))<=.03000001
    reported={(r['suite'],r['model'],r['metric']):r for r in read('summary.csv')}
    seen=set()
    for model in ('aimv2','dinov2'):
        outcomes=defaultdict(dict)
        for r in read(model+'_predictions.csv'):
            design=by_name[r['image_id']][r['condition']]
            assert design['input_sha256']==r['input_sha256'] and design['label']==r['label']
            assert r['condition'] not in outcomes[r['image_id']]
            outcomes[r['image_id']][r['condition']]=int(r['prediction']==r['label'])
        assert all(set(outcomes[n])==set(cs) for n,cs in by_name.items())
        for suite,selected in [('direct',direct),('regional',regional)]:
            breeds=defaultdict(lambda:defaultdict(list))
            for n in selected:
                scores=outcomes[n]; center=scores['center']
                if suite=='direct':
                    alt=(scores['relocated1']+scores['relocated2'])/2
                    sample=dict(center=center,relocated=alt,center_cost=center-alt)
                else:
                    sample={k:scores[k] for k in ('center','animal','background','both')}
                    animal,bg,both=(sample[k] for k in ('animal','background','both'))
                    sample.update(animal_cost=(center+bg-animal-both)/2,background_cost=(center+animal-bg-both)/2,
                                  animal_minus_background_cost=bg-animal,factor_interaction=center-animal-bg+both)
                for metric,val in sample.items():
                    breeds[metric][by_name[n]['center']['label']].append(val)
            for metric,values in breeds.items():
                key=(suite,model,metric); seen.add(key); actual=reported[key]
                assert int(actual['n'])==len(selected) and int(actual['breeds'])==len(values)==37
                assert abs(mean(mean(v) for v in values.values())-float(actual['estimate']))<1e-9
    assert seen==set(reported)
    print(f'All {len(seen)} estimates verified on {len(direct)} direct and {len(regional)} regional photos; {len(direct&regional)} overlap. Pixel replay: {raw}.')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--pixels',action='store_true')
    check(p.parse_args().pixels)
