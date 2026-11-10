"""Foreground-conditioned accuracy with image-clustered, breed-stratified intervals.

Read saved predictions only. Repeated masks never become independent samples.
New inference runs are included only after their complete integration audit passes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/occlusion_completion'
MODELS=['aimv2','dinov2']
PATTERNS=['prefix','suffix','center','random']
COLORS=['#087f8c','#d46b29']
MEASURES=['object_visibility','background_visibility','head_visibility','body_visibility','head_foreground_fraction']
BOOT=10000


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def read_paired(run):
    base=ROOT/'results'/run
    if run!='extension_v2':
        audit=json.loads((base/'integration_audit.json').read_text())
        assert audit['passed'] and audit['completed_models']==MODELS
    conditions=pd.read_csv(base/'conditions.csv',keep_default_na=False)
    assert not conditions.condition_id.duplicated().any()
    result=conditions.copy()
    for model in MODELS:
        p=pd.read_csv(base/f'{model}_predictions.csv',keep_default_na=False)
        assert len(p)==len(conditions) and not p.condition_id.duplicated().any()
        p=p.set_index('condition_id').loc[conditions.condition_id].reset_index()
        for col in conditions:
            assert np.array_equal(conditions[col].astype(str),p[col].astype(str)),(run,col)
        assert np.array_equal(p.correct.to_numpy(),(p.prediction==p.label).astype(int).to_numpy())
        assert p.target_probability.between(0,1).all()
        result[model]=p.correct.to_numpy(dtype=float)
        result[model+'_prediction']=p.prediction.to_numpy()
    for col in MEASURES:
        if col not in result:result[col]=np.nan
        result[col]=pd.to_numeric(result[col],errors='coerce')
    assert result.object_visibility.between(0,1).all()
    result['source_run']=run
    return result


def image_average(frame):
    keys=['cohort','image_id','label','fill','fraction','pattern']
    return frame[frame.suite=='standard'].groupby(keys,as_index=False)[MODELS+MEASURES].mean()


class ImageBootstrap:
    def __init__(self,frame,repetitions=BOOT,seed=6692032):
        sample=frame[['image_id','label']].drop_duplicates().sort_values('image_id')
        assert not sample.image_id.duplicated().any()
        self.ids=sample.image_id.tolist();self.index={v:i for i,v in enumerate(self.ids)}
        self.labels=sample.label.to_numpy();self.repetitions=repetitions
        rng=np.random.default_rng(seed)
        self.counts=np.zeros((repetitions,len(sample)),dtype=np.float64)
        for label in sorted(set(self.labels)):
            ix=np.flatnonzero(self.labels==label)
            self.counts[:,ix]=rng.multinomial(len(ix),np.ones(len(ix))/len(ix),size=repetitions)

    def estimate(self,frame,weights=None,equal_breed=False):
        """Ratio estimator, jointly weighted for both models and paired difference."""
        if len(frame)==0:return None
        ix=np.array([self.index[x] for x in frame.image_id])
        weights=np.ones(len(frame)) if weights is None else np.asarray(weights,dtype=float)
        if equal_breed:
            # Used only for a paired cohort with one row per original image.
            assert len(np.unique(ix))==len(ix)
            labels=frame.label.to_numpy()
            weights=weights/np.array([(labels==x).sum() for x in labels])
        den=np.zeros(len(self.ids));num=np.zeros((len(self.ids),3))
        value=frame[MODELS].to_numpy(float)
        value=np.column_stack([value,value[:,0]-value[:,1]])
        np.add.at(den,ix,weights);np.add.at(num,ix,weights[:,None]*value)
        point=num.sum(axis=0)/den.sum()
        draws_den=self.counts@den
        valid=draws_den>0
        boot=(self.counts[valid]@num)/draws_den[valid,None]
        ci=np.quantile(boot,[.025,.975],axis=0) if valid.mean()>=.95 else np.full((2,3),np.nan)
        return point,ci,boot,float(1-valid.mean())


def write(frame,name):
    frame.to_csv(OUT/name,index=False,float_format='%.12g')


def summarize(per,bootstrap):
    records=[]
    for key,g in per.groupby(['cohort','fraction','fill','pattern']):
        point,ci,boot,empty=bootstrap.estimate(g)
        for j,metric in enumerate(MODELS+['aim_minus_dino']):
            r=dict(zip(['cohort','fraction','fill','pattern'],key))
            r.update(metric=metric,estimate=point[j],ci_low=ci[0,j],ci_high=ci[1,j],
                     n_images=g.image_id.nunique(),n_breeds=g.label.nunique(),
                     foreground_mean=g.object_visibility.mean(),empty_bootstrap_fraction=empty)
            if metric=='aim_minus_dino' and r['pattern'] in ['center','random']:
                q=.05/(2*12);bounds=np.quantile(boot[:,j],[q,1-q])
                r.update(familywise_ci_low=bounds[0],familywise_ci_high=bounds[1],family_size=12)
            records.append(r)
    return pd.DataFrame(records)


def bins(frame,bootstrap,width,convention='image_average',head_thirds=False):
    records=[]
    frame=frame[frame.pattern!='clean'].copy()
    # Multiply by integer bin count: .6 / .2 can round below 3 in binary floats.
    bin_count=round(1/width)
    frame['fg_bin']=np.minimum((frame.object_visibility*bin_count).astype(int),bin_count-1)
    keys=['cohort','fraction','fill','pattern','fg_bin']
    if head_thirds:
        frame=frame[frame.head_visibility.notna()].copy()
        frame['head_third']=np.minimum((frame.head_visibility*3).astype(int),2)
        keys+=['head_third']
    for key,g in frame.groupby(keys):
        weights=np.full(len(g),1/3) if convention=='individual_repeats' and g.pattern.iloc[0]=='random' else np.ones(len(g))
        record=dict(zip(keys,key));n=g.image_id.nunique()
        record.update(bin_width=width,convention=convention,n_images=n,n_rows=len(g),
                      n_breeds=g.label.nunique(),sparse=n<20,estimable=n>=5,
                      foreground_mean=float(np.average(g.object_visibility,weights=weights)),
                      foreground_min=g.object_visibility.min(),foreground_q25=g.object_visibility.quantile(.25),
                      foreground_median=g.object_visibility.median(),foreground_q75=g.object_visibility.quantile(.75),
                      foreground_max=g.object_visibility.max(),
                      breed_counts=json.dumps(g.drop_duplicates('image_id').label.value_counts().sort_index().to_dict()))
        if head_thirds:record['head_mean']=float(np.average(g.head_visibility,weights=weights))
        if n>=5:
            point,ci,_,empty=bootstrap.estimate(g,weights)
            record['empty_bootstrap_fraction']=empty
        for j,metric in enumerate(MODELS+['aim_minus_dino']):
            r=dict(record,metric=metric,estimate=point[j] if n>=5 else np.nan,
                   ci_low=ci[0,j] if n>=5 else np.nan,ci_high=ci[1,j] if n>=5 else np.nan)
            records.append(r)
    return pd.DataFrame(records)


def support_table(bin_table):
    rows=[]
    b=bin_table[(bin_table.metric=='aimv2')&(bin_table.convention=='image_average')]
    for key,g in b.groupby(['cohort','fraction','fill','bin_width']):
        width=key[-1]
        counts=g.pivot(index='fg_bin',columns='pattern',values='n_images').reindex(index=range(round(1/width)),columns=PATTERNS).fillna(0)
        common=counts.index[(counts>=5).all(axis=1)].tolist()
        minimum=counts.loc[common].min(axis=1)
        weights=minimum/minimum.sum() if len(common) else minimum
        allbins=bin_table[(bin_table.cohort==key[0])&(bin_table.fraction==key[1])&(bin_table.fill==key[2])&(bin_table.bin_width==width)&(bin_table.convention=='image_average')]
        for pattern in PATTERNS:
            for metric in MODELS+['aim_minus_dino']:
                a=allbins[(allbins.pattern==pattern)&(allbins.metric==metric)].set_index('fg_bin')
                row=dict(zip(['cohort','fraction','fill','bin_width'],key))
                row.update(pattern=pattern,metric=metric,common_bins=';'.join(map(str,common)),
                           n_retained=int(counts.loc[common,pattern].sum()),n_total=int(counts[pattern].sum()),
                           retained_fraction=float(counts.loc[common,pattern].sum()/counts[pattern].sum()),
                           standardized_accuracy=float((a.loc[common,'estimate']*weights).sum()) if common else np.nan,
                           estimand='Common-bin minimum-count weighted descriptive mean; no causal adjustment')
                rows.append(row)
    return pd.DataFrame(rows)


def curve_figures(b,cohort):
    b=b[(b.cohort==cohort)&(b.bin_width==.2)&(b.convention=='image_average')]
    for (frac,fill),t in b.groupby(['fraction','fill']):
        fig,axes=plt.subplots(2,4,figsize=(14,6.3),gridspec_kw={'height_ratios':[3,1.1]},sharex=True)
        for col,pattern in enumerate(PATTERNS):
            ax=axes[0,col];counts=t[(t.pattern==pattern)&(t.metric=='aimv2')].sort_values('fg_bin')
            for j,model in enumerate(MODELS):
                q=t[(t.pattern==pattern)&(t.metric==model)].sort_values('fg_bin')
                # NaNs intentionally break lines at unobserved/suppressed cells.
                allq=q.set_index('fg_bin').reindex(range(5))
                ax.plot(allq.foreground_mean*100,allq.estimate*100,color=COLORS[j],lw=1.5,label=model.upper().replace('V','v'))
                valid=q[q.estimable]
                ax.errorbar(valid.foreground_mean*100,valid.estimate*100,
                            yerr=np.maximum(0,np.stack([valid.estimate-valid.ci_low,valid.ci_high-valid.estimate])*100),
                            fmt='none',ecolor=COLORS[j],capsize=3,lw=1)
                for sparse,sub in valid.groupby('sparse'):
                    ax.scatter(sub.foreground_mean*100,sub.estimate*100,s=34,marker='o',
                               facecolors='white' if sparse else COLORS[j],edgecolors=COLORS[j],zorder=3)
            ax.set_title({'prefix':'Prefix / top','suffix':'Suffix / bottom','center':'Center','random':'Random'}[pattern]);ax.set_ylim(-3,103);ax.set_xlim(0,100);ax.grid(alpha=.18)
            for r in counts.itertuples():
                axes[1,col].bar((r.fg_bin+.5)*20,r.n_images,width=17,color='#a4bdc4')
                axes[1,col].text((r.fg_bin+.5)*20,r.n_images+max(counts.n_images.max()*.025,1),str(r.n_images),ha='center',fontsize=8)
            axes[1,col].set_ylim(0,max(10,counts.n_images.max()*1.28));axes[1,col].set_xlabel('Animal foreground visible (%)')
        axes[0,0].set_ylabel('Breed accuracy (%)');axes[1,0].set_ylabel('Original images');axes[0,0].legend(fontsize=9,loc='lower right')
        fig.suptitle(f'{cohort}: {frac:.0%} image visible | {"gray" if fill==128 else "black"} fill',fontsize=16,y=.98)
        fig.text(.5,.015,'20-point foreground bins; pointwise 95% image-bootstrap intervals. Hollow points: 5–19 images; <5 suppressed. Random repeats averaged per image.',ha='center',fontsize=9)
        fig.tight_layout(rect=[0,.04,1,.94]);savefig(fig,f'{cohort}_foreground_{int(frac*100)}_fill{fill}')


def savefig(fig,name):
    fig.savefig(OUT/'figures'/f'{name}.png',dpi=170,bbox_inches='tight')
    fig.savefig(OUT/'figures'/f'{name}.pdf',bbox_inches='tight');plt.close(fig)


def ranking_figure(summary,cohort):
    data=summary[(summary.cohort==cohort)&(summary.pattern!='clean')&(summary.metric=='aim_minus_dino')]
    fig,axes=plt.subplots(1,2,figsize=(11,4.8),sharey=True)
    for ax,fill in zip(axes,[128,0]):
        for i,pattern in enumerate(PATTERNS):
            t=data[(data.fill==fill)&(data.pattern==pattern)].sort_values('fraction')
            ax.errorbar(t.fraction*100+(i-1.5)*.8,t.estimate*100,
                        yerr=np.maximum(0,np.stack([t.estimate-t.ci_low,t.ci_high-t.estimate])*100),fmt='o-',label=pattern,capsize=3)
        ax.axhline(0,color='#666',lw=.9);ax.set_xticks([25,50,75]);ax.set_xlim(20,80);ax.set_xlabel('Image visible (%)');ax.set_title('Gray fill' if fill==128 else 'Black fill');ax.grid(alpha=.15)
    axes[0].set_ylabel('AIMv2 minus DINOv2 accuracy (percentage points)');axes[1].legend()
    fig.suptitle(f'{cohort}: model ordering across visibility budgets')
    fig.text(.5,.01,'Above zero favors AIMv2; below zero favors DINOv2. Pointwise paired 95% intervals; full contrast family also saved.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.05,1,.94]);savefig(fig,f'{cohort}_model_ordering')


def standard_regions(per):
    """Connect head-region measurements to all standard patterns on the new cohort."""
    frame=per[(per.cohort=='new_head')&(per.pattern!='clean')]
    if frame.empty:return
    records=[]
    for (fraction,fill,pattern),g in frame.groupby(['fraction','fill','pattern']):
        r=dict(fraction=fraction,fill=fill,pattern=pattern,n_images=g.image_id.nunique())
        for field in MEASURES+MODELS:
            r[field]=float(g[field].mean())
            r[field+'_n_images']=int(g.loc[g[field].notna(),'image_id'].nunique())
        records.append(r)
    table=pd.DataFrame(records);write(table,'standard_region_visibility.csv')
    fig,axes=plt.subplots(1,3,figsize=(13,4.8),sharey=True)
    fields=['object_visibility','head_visibility','body_visibility']
    for ax,fraction in zip(axes,[.25,.5,.75]):
        q=table[(table.fraction==fraction)&(table.fill==128)].set_index('pattern').loc[PATTERNS]
        for i,(field,label,color) in enumerate(zip(fields,['Animal','Head ROI','Other animal'],['#627985','#087f8c','#d46b29'])):
            ax.bar(np.arange(4)+(i-1)*.24,q[field]*100,.24,label=label,color=color)
        ax.set_xticks(np.arange(4),['Top','Bottom','Center','Random']);ax.set_ylim(0,105);ax.set_title(f'{fraction:.0%} image visible');ax.grid(axis='y',alpha=.15)
    axes[0].set_ylabel('Mean region visible (%)');axes[2].legend(fontsize=8,loc='lower right')
    fig.suptitle('New annotated cohort: retained regions across all four patterns',fontsize=15)
    body_n=frame.loc[frame.body_visibility.notna(),'image_id'].nunique()
    fig.text(.5,.01,f'185 original images; random repeats averaged per image. Head ROI is a bounding-box proxy.\nCoverage uses region-specific denominators; other-animal coverage is defined for {body_n} of 185 images.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.08,1,.94]);savefig(fig,'new_head_standard_regions')


def pair_summaries(frame):
    records=[]
    for (cohort,pair_type,fill),g in frame[frame.suite=='paired'].groupby(['cohort','pair_type','fill']):
        roles=['high','low'] if pair_type in ['head_contrast','object_contrast'] else ['a','b']
        a,b=[g[g.pair_role==r].sort_values('image_id').reset_index(drop=True) for r in roles]
        assert len(a)==len(b) and np.array_equal(a.image_id,b.image_id)
        bootstrap=ImageBootstrap(a)
        for model in MODELS:
            tmp=a[['image_id','label']].copy();tmp['aimv2']=a[model];tmp['dinov2']=b[model]
            point,ci,_,_=bootstrap.estimate(tmp,equal_breed=True)
            r=dict(cohort=cohort,pair_type=pair_type,fill=fill,model=model,n_images=len(a),n_breeds=a.label.nunique(),role_a=roles[0],role_b=roles[1],
                   accuracy_a=point[0],accuracy_b=point[1],difference=point[2],difference_low=ci[0,2],difference_high=ci[1,2])
            tmp['aimv2']=(a[model]!=b[model]).astype(float);tmp['dinov2']=0.
            flip,fc,_,_=bootstrap.estimate(tmp,equal_breed=True)
            r.update(correctness_flip_rate=flip[0],flip_low=fc[0,0],flip_high=fc[1,0])
            for col in MEASURES:
                if a[col].notna().all() and b[col].notna().all():
                    r[col+'_a']=a[col].mean();r[col+'_b']=b[col].mean()
                    r[col+'_mean_pair_gap']=(a[col]-b[col]).abs().mean();r[col+'_max_pair_gap']=(a[col]-b[col]).abs().max()
            records.append(r)
    return pd.DataFrame(records)


def region_figures(pairs):
    for cohort in ['auxiliary_head','new_head']:
        p=pairs[(pairs.cohort==cohort)&(pairs.pair_type=='head_contrast')&(pairs.fill==128)]
        if p.empty:continue
        fig,axes=plt.subplots(1,2,figsize=(11,5))
        x=np.arange(4);r=p.iloc[0]
        fields=['object_visibility','head_visibility','body_visibility','background_visibility']
        for offset,role,color,label in [(-.18,'a',COLORS[0],'Higher head coverage'),(.18,'b',COLORS[1],'Lower head coverage')]:
            vals=[r[f+'_'+role]*100 for f in fields]
            bars=axes[0].bar(x+offset,vals,.36,color=color,label=label);axes[0].bar_label(bars,fmt='%.1f%%',fontsize=8,padding=3)
        axes[0].set_xticks(x,['Animal','Head ROI','Other animal','Background']);axes[0].set_ylim(0,110);axes[0].set_ylabel('Region visible (%)');axes[0].legend(fontsize=8,loc='upper right')
        for j,model in enumerate(MODELS):
            q=p[p.model==model].iloc[0]
            bars=axes[1].bar(np.array([0,1])+(j-.5)*.32,[q.accuracy_a*100,q.accuracy_b*100],.32,color=COLORS[j],label=model)
            axes[1].bar_label(bars,fmt='%.1f%%',padding=3,fontsize=9)
        axes[1].set_xticks([0,1],['Higher head coverage','Lower head coverage']);axes[1].set_ylim(0,110);axes[1].set_ylabel('Breed accuracy (%)');axes[1].legend(fontsize=9)
        fig.suptitle(f'{cohort}: {int(r.n_images)} eligible same-image pairs, 75% image visible',fontsize=14)
        fig.text(.5,.015,'Head ROI = head box intersected with foreground. Other animal regions and background change too; this is not an isolated head effect.',ha='center',fontsize=9)
        fig.tight_layout(rect=[0,.05,1,.93]);savefig(fig,f'{cohort}_region_bundle')


def run(include_new=True):
    OUT.mkdir(exist_ok=True);(OUT/'figures').mkdir(exist_ok=True)
    runs=['extension_v2']
    if include_new:
        for name in ['completion_primary','completion_head']:
            if (ROOT/f'results/{name}/integration_audit.json').exists():runs.append(name)
    raw=pd.concat([read_paired(run) for run in runs],ignore_index=True)
    assert not raw.duplicated(['cohort','image_id','suite','pattern','fraction','repeat','pair_type','pair_role','fill']).any()
    per=image_average(raw)
    write(raw,'analysis_conditions.csv');write(per,'image_averages.csv')
    summaries=[];allbins=[];regions=[]
    for cohort in ['primary','new_head']:
        frame=per[per.cohort==cohort]
        if frame.empty:continue
        bootstrap=ImageBootstrap(frame)
        summaries.append(summarize(frame,bootstrap))
        for width in [.2,.1]:allbins.append(bins(frame,bootstrap,width))
        individual=raw[(raw.cohort==cohort)&(raw.suite=='standard')]
        allbins.append(bins(individual,bootstrap,.2,'individual_repeats'))
        if cohort=='new_head':regions.append(bins(frame,bootstrap,.2,head_thirds=True))
        print('Analyzed',cohort,flush=True)
    summary=pd.concat(summaries,ignore_index=True);b=pd.concat(allbins,ignore_index=True)
    write(summary,'accuracy_summary.csv');write(b,'foreground_bins.csv');write(support_table(b),'common_support.csv')
    if regions:write(pd.concat(regions,ignore_index=True),'head_thirds.csv')
    pairs=pair_summaries(raw);write(pairs,'pair_measurements.csv')
    # Independently reproduce the prior standard and paired headline estimates.
    old=pd.read_csv(ROOT/'results/extension_v2/summary.csv')
    old=old[(old.cohort=='primary')&(old.pattern!='clean')]
    for r in old.itertuples():
        x=summary[(summary.cohort=='primary')&(summary.fraction==.25)&(summary.fill==r.fill)&(summary.pattern==r.pattern)&(summary.metric==r.model)]
        assert len(x)==1 and abs(x.estimate.iloc[0]-r.estimate)<1e-12
    oldpairs=pd.read_csv(ROOT/'results/extension_v2/paired_summary.csv')
    for r in oldpairs.itertuples():
        x=pairs[(pairs.cohort==r.cohort)&(pairs.pair_type==r.pair_type)&(pairs.fill==r.fill)&(pairs.model==r.model)].iloc[0]
        assert abs(x.accuracy_a-r.accuracy_a)<1e-12 and abs(x.accuracy_b-r.accuracy_b)<1e-12
    for cohort in summary.cohort.unique():curve_figures(b,cohort);ranking_figure(summary,cohort)
    region_figures(pairs)
    standard_regions(per)
    sources={f'{run}/{file}':digest(ROOT/'results'/run/file) for run in runs for file in ['conditions.csv','aimv2_predictions.csv','dinov2_predictions.csv']}
    audit=dict(passed=True,runs=runs,original_conditions=len(raw),original_images_by_cohort=raw.groupby('cohort').image_id.nunique().to_dict(),
               joins_one_to_one=True,shared_input_metadata_verified=True,old_headline_estimates_reproduced=True,
               bootstrap_repetitions=BOOT,bootstrap_unit='Original image, resampled within breed',
               curve_estimand='Image-weighted accuracy conditional on foreground bin; random repeats averaged before main binning',
               pair_estimand='Equal represented-breed average among eligible image pairs',
               confidence_intervals='Pointwise except explicit 12-contrast model-ordering families; fixed systems',
               source_hashes=sources,script_sha256=digest(Path(__file__)))
    (OUT/'measurement_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k!='source_hashes'},indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--existing-only',action='store_true');a=p.parse_args();run(not a.existing_only)
