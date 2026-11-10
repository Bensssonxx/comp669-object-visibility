"""Prepare blind masks, run the frozen models and summarize a paired region experiment."""
import argparse
import hashlib
import json
from pathlib import Path
from functools import lru_cache

import numpy as np
import pandas as pd
from PIL import features

from occlusion_visibility.data import load_image, read_split, sha256_file
from occlusion_visibility.masks import stable_seed, apply_mask
from occlusion_visibility.experiment import decode_mask
from occlusion_visibility.encoders import FrozenEncoder
from extension_v2 import predict, cache_binding
from patch_relocation import CENTER, propose
from final_sensitivity import intervals

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/region_swap'
PROTOCOL = ROOT/'docs/REGION_SWAP_PROTOCOL.md'
MODELS = ['aimv2','dinov2']
REGIONAL = ['center','animal','background','both']
RUNS = ['pilot_v1','extension_v2','completion_primary','completion_head']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pixels(grid):
    return grid.reshape(16,16).repeat(14, axis=0).repeat(14, axis=1)


def tiles(trimap, value):
    return (trimap==value).reshape(16,14,16,14).sum(axis=(1,3)).ravel()


def swaps(name, counts):
    toggles = []
    for label, values in enumerate(counts, 1):
        pure = values == 196
        visible = np.flatnonzero(pure & CENTER)
        hidden = np.flatnonzero(pure & ~CENTER)
        if min(len(visible),len(hidden)) < 4:
            return {}
        rng = np.random.default_rng(stable_seed('regional-swaps-669',name,label))
        toggle = np.zeros(256,dtype=bool)
        toggle[rng.choice(visible,4,replace=False)] = True
        toggle[rng.choice(hidden,4,replace=False)] = True
        toggles.append(toggle)
    animal,background = toggles
    return dict(zip(REGIONAL,[CENTER,CENTER ^ animal,CENTER ^ background,CENTER ^ animal ^ background]))


def design_hashes():
    paths = [PROTOCOL,Path(__file__),ROOT/'scripts/patch_relocation.py',OUT/'candidates.csv',OUT/'conditions.csv']
    return {str(p.relative_to(ROOT)):sha256_file(p) for p in paths}


def write_fixed(path, text):
    if path.exists() and path.read_text()!=text:
        raise ValueError(f'Design differs from saved {path}')
    path.write_text(text)


def prepare():
    assert features.version_codec('jpg')=='9.0' and features.version_feature('libjpeg_turbo') is None
    old = [r for run in RUNS for r in json.loads((ROOT/'results'/run/'manifest.json').read_text())]
    seen = {r['image_sha256'] for r in old}
    blocked = {r['image_id'] for r in old}
    ordered = sorted(read_split(ROOT/'data/raw/annotations/test.txt'),key=lambda r:(r['label'],stable_seed('fresh-669-region', r['image_id'])))
    n_direct,n_region = np.zeros((2,37),dtype=int)
    pool,rows = [],[]
    for r in ordered:
        name,label = r['image_id'],r['label']
        entry = dict(image_id=name,label=label,direct=False,regional=False,regional_eligible=False)
        pool.append(entry)
        if name in blocked:
            entry['reason']='previous ID'
            continue
        file_hash=sha256_file(ROOT/f'data/raw/images/{name}.jpg')
        entry['jpeg_sha256']=file_hash
        if file_hash in seen:
            entry['reason']='previous or duplicate bytes'
            continue
        seen.add(file_hash)
        rgb,trimap=load_image(ROOT,name)
        counts=[tiles(trimap,1),tiles(trimap,2)]
        if not counts[0].sum() or not np.isin(trimap,[1,2,3]).all():
            entry['reason']='trimap'
            continue
        candidates=swaps(name,counts)
        entry['reason']='valid'
        entry['regional_eligible']=bool(candidates)
        entry['direct']=bool(n_direct[label]<10)
        entry['regional']=bool(candidates and n_region[label]<10)
        n_direct[label]+=entry['direct']
        n_region[label]+=entry['regional']
        chosen=candidates.copy() if entry['regional'] else {}
        if entry['direct']:
            variants=propose(counts[0],name)
            entry['direct_eligible']=bool(variants)
            if variants:
                chosen.update(center=CENTER,relocated1=variants[0],relocated2=variants[1])
        for condition,grid in chosen.items():
            assert grid.sum()==64
            visible=pixels(grid)
            if condition in REGIONAL:
                assert all(c @ grid.astype(int)==c @ CENTER.astype(int) for c in counts)
            rows.append(dict(image_id=name,label=label,condition=condition,mask_hex=np.packbits(grid).tobytes().hex(),
                             rgb_sha256=digest(rgb.tobytes()),trimap_sha256=digest(trimap.tobytes()),
                             input_sha256=digest(apply_mask(rgb,visible,128).tobytes()),
                             animal_pixels=int(counts[0][grid].sum()),background_pixels=int(counts[1][grid].sum())))
    OUT.mkdir(exist_ok=True)
    assert (n_direct==10).all()
    for stem,items in [('candidates',pool),('conditions',rows)]:
        write_fixed(OUT/(stem+'.csv'),pd.DataFrame(items).to_csv(index=False))
    write_fixed(OUT/'design_lock.json',json.dumps(design_hashes(),indent=2)+'\n')
    print('Direct and regional samples:',n_direct.sum(),n_region.sum(),'mask rows:',len(rows),flush=True)


@lru_cache(maxsize=4)
def image(name,rgb_hash):
    rgb,_=load_image(ROOT,name)
    assert digest(rgb.tobytes())==rgb_hash
    return rgb


def infer(model):
    assert json.loads((OUT/'design_lock.json').read_text())==design_hashes()
    rows=pd.read_csv(OUT/'conditions.csv')
    source=ROOT/'results/completion_primary'
    cfg=json.loads((source/'config.json').read_text())
    binding=json.loads((source/f'features/{model}.json').read_text())
    assert binding==cache_binding(ROOT,source,cfg,range(binding['shape'][0]),model)
    encoder=FrozenEncoder(ROOT,model,'mps')
    outputs=[]
    with np.load(source/f'probes/{model}_linear.npz') as probe:
        for start in range(0,len(rows),8):
            inputs=[]
            for r in rows.iloc[start:start+8].itertuples():
                inp=apply_mask(image(r.image_id,r.rgb_sha256),decode_mask(r.mask_hex,224,14),128)
                assert digest(inp.tobytes())==r.input_sha256
                inputs.append(inp)
            encoded=encoder.encode(np.stack(inputs))
            assert np.isfinite(encoded).all() and np.allclose(np.linalg.norm(encoded,axis=1),1,atol=1e-5)
            predictions,_=predict(encoded,probe)
            outputs.extend(predictions.tolist())
            if start%512==0: print(model,start,'/',len(rows),flush=True)
    result=rows[['image_id','condition','input_sha256','label']].assign(prediction=outputs)
    dest=OUT/f'{model}_predictions.csv'
    tmp=dest.with_suffix('.tmp')
    result.to_csv(tmp,index=False)
    tmp.replace(dest)
    print(model,'complete',len(result),flush=True)


def summarize():
    assert design_hashes()==json.loads((OUT/'design_lock.json').read_text())
    rows=pd.read_csv(OUT/'conditions.csv')
    pool=pd.read_csv(OUT/'candidates.csv')
    for m in MODELS:
        prediction=pd.read_csv(OUT/f'{m}_predictions.csv')
        keys=['image_id','condition','label','input_sha256']
        pd.testing.assert_frame_equal(rows[keys],prediction[keys])
        assert prediction.prediction.between(0,36).all()
        rows[m]=prediction.prediction.eq(rows.label).astype(float)
    result=[]
    for suite,subset in [('direct',pool.direct & pool.direct_eligible.eq(True)),('regional',pool.regional)]:
        ids=pool.loc[subset].set_index('image_id').label.sort_index()
        rng=np.random.default_rng(6691111)
        breeds=ids.unique()
        weights=np.zeros((10000,len(ids)))
        for breed in breeds:
            ix=np.flatnonzero(ids.values==breed)
            weights[:,ix]=rng.multinomial(len(ix),np.full(len(ix),1/len(ix)),size=len(weights))/(len(breeds)*len(ix))
        for m in MODELS:
            wide=rows.pivot(index='image_id',columns='condition',values=m).loc[ids.index]
            if suite=='direct':
                assert wide[['center','relocated1','relocated2']].notna().all().all()
                x=wide[['center']].assign(relocated=wide[['relocated1','relocated2']].mean(axis=1))
                x['center_cost']=x.center-x.relocated
                primary='center_cost'
            else:
                x=wide[REGIONAL].copy()
                assert x.notna().all().all()
                x['animal_cost']=(x.center-x.animal+x.background-x.both)/2
                x['background_cost']=(x.center-x.background+x.animal-x.both)/2
                x['animal_minus_background_cost']=x.animal_cost-x.background_cost
                x['factor_interaction']=x.center-x.animal-x.background+x.both
                primary='animal_minus_background_cost'
            draws=weights@x.to_numpy()
            pt=x.groupby(ids).mean().mean()
            for i,metric in enumerate(x):
                lo,hi=intervals(draws[:,i])
                adj=intervals(draws[:,i],2) if metric==primary else (None,None)
                result.append(dict(suite=suite,model=m,metric=metric,n=len(ids),breeds=len(breeds),
                                   estimate=pt[metric],low=lo,high=hi,adjusted_low=adj[0],adjusted_high=adj[1]))
    pd.DataFrame(result).to_csv(OUT/'summary.csv',index=False,float_format='%.10g')
    print(pd.DataFrame(result).dropna().to_string(index=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare',*MODELS,'summarize'])
    stage=parser.parse_args().stage
    if stage=='prepare': prepare()
    elif stage=='summarize': summarize()
    else: infer(stage)
