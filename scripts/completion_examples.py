"""Display real masked inputs with exact annotation coverage and selection records."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from occlusion_visibility.data import load_image
from occlusion_visibility.experiment import decode_mask
from occlusion_visibility.masks import apply_mask,visibility_mask,stable_seed,coverage
import extension_v2 as ext

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/occlusion_completion'


def save(fig,name):
    fig.savefig(OUT/'figures'/f'{name}.png',dpi=160,bbox_inches='tight')
    fig.savefig(OUT/'figures'/f'{name}.pdf',bbox_inches='tight');plt.close(fig)


def budget_examples():
    manifest=json.loads((ROOT/'results/extension_v2/manifest.json').read_text())
    name=next(r['image_id'] for r in manifest if r['cohort']=='primary')
    rgb,trimap=load_image(ROOT,name)
    fig,axes=plt.subplots(3,4,figsize=(12,12))
    measures=[]
    for i,fraction in enumerate([.25,.5,.75]):
        for j,pattern in enumerate(['prefix','suffix','center','random']):
            mask=visibility_mask(pattern,fraction,seed=stable_seed(6692026,name,0))
            q=coverage(trimap,mask);ax=axes[i,j]
            ax.imshow(apply_mask(rgb,mask,128));ax.set_xticks([]);ax.set_yticks([])
            ax.set_title(f'{pattern} | {fraction:.0%} image visible',fontsize=11)
            ax.set_xlabel(f'Animal visible: {q["object_visibility"]:.1%}',fontsize=11)
            measures.append(dict(image_id=name,pattern=pattern,image_visibility=fraction,**q))
    fig.suptitle(f'Same original image, exact visibility budgets: {name}',fontsize=16)
    fig.text(.5,.01,'First primary manifest image, chosen without predictions. Random repeat 0. Gray pixels replace hidden regions; no tokens are removed.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.035,1,.96],h_pad=3.5);save(fig,'input_budget_examples')
    return measures


def head_examples(raw,cohort):
    manifest_all=json.loads((ROOT/'results/extension_v2/manifest.json').read_text())
    breed={r['label']:r['image_id'].rsplit('_',1)[0].replace('_',' ') for r in manifest_all}
    g=raw[(raw.cohort==cohort)&(raw.pair_type=='head_contrast')&(raw.fill==128)]
    if g.empty:return []
    high=g[g.pair_role=='high'].set_index('image_id').sort_index();low=g[g.pair_role=='low'].set_index('image_id').loc[high.index]
    if cohort=='auxiliary_head':
        first=json.loads((ROOT/'results/extension_v2/design_example_selection.json').read_text())['auxiliary_image_id']
    else:
        manifest=json.loads((ROOT/'results/completion_head/manifest.json').read_text())
        first=next(r['image_id'] for r in manifest if r['image_id'] in high.index)
    selected=[(first,'Annotation-only first eligible manifest image')]
    rules=[('AIMv2 correct-to-wrong',(high.aimv2==1)&(low.aimv2==0)),
           ('Both models wrong in both versions',(high.aimv2==0)&(low.aimv2==0)&(high.dinov2==0)&(low.dinov2==0))]
    for reason,mask in rules:
        names=[n for n in high.index[mask] if n not in [a for a,_ in selected]]
        if names:selected.append((names[0],'Outcome-selected illustration: '+reason))
    fig,axes=plt.subplots(len(selected),3,figsize=(12,5.3*len(selected)),squeeze=False)
    records=[]
    for i,(name,reason) in enumerate(selected):
        rgb,trimap=load_image(ROOT,name);head,_=ext.load_head(ROOT,name,trimap)
        ax=axes[i,0];ax.imshow(rgb);ax.contour(head,levels=[.5],colors=['#00ffb3'],linewidths=1.3)
        ax.set_title(name,fontsize=12);ax.set_xlabel('Original image; green outline = head ROI\n'+reason.replace(': ',':\n'),fontsize=9)
        for j,(role,table) in enumerate([('Higher head',high),('Lower head',low)],start=1):
            r=table.loc[name];mask=decode_mask(r.mask_hex,224,14);ax=axes[i,j]
            ax.imshow(apply_mask(rgb,mask,128));ax.set_title(role,fontsize=12)
            aim_breed=breed[int(r.aimv2_prediction)];dino_breed=breed[int(r.dinov2_prediction)]
            label=f'Animal {r.object_visibility:.1%} | Head {r.head_visibility:.1%}\nOther animal {r.body_visibility:.1%} | Background {r.background_visibility:.1%}\nAIMv2: {aim_breed} ({"correct" if r.aimv2 else "wrong"})\nDINOv2: {dino_breed} ({"correct" if r.dinov2 else "wrong"})'
            ax.set_xlabel(label,fontsize=9)
            records.append(dict(cohort=cohort,image_id=name,selection=reason,condition_id=r.condition_id,
                                role=role,animal=r.object_visibility,head=r.head_visibility,body=r.body_visibility,
                                background=r.background_visibility,aim_correct=int(r.aimv2),dino_correct=int(r.dinov2),
                                true_breed=breed[int(r.label)],aim_prediction=aim_breed,dino_prediction=dino_breed))
        for ax in axes[i]:ax.set_xticks([]);ax.set_yticks([])
    fig.suptitle(f'{cohort}: same-size square masks, 75% image visible',fontsize=16)
    fig.text(.5,.005,'Selected examples illustrate behavior, not its prevalence. Head ROI is a bounding-box proxy; other regions change along with it.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.025,1,.97],h_pad=5.0);save(fig,f'{cohort}_actual_pairs')
    return records


if __name__=='__main__':
    raw=pd.read_csv(OUT/'analysis_conditions.csv')
    result={'budget_selection':'First primary manifest image; independent of outcomes','budget_measurements':budget_examples(),
            'head_examples':sum([head_examples(raw,c) for c in ['auxiliary_head','new_head']],[])}
    (OUT/'example_selection.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Saved actual-input figures and selection audit.')
