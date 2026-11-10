"""Write an English report from complete, audited saved result tables."""
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/occlusion_completion'


def table(rows,headers):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])


def main():
    audit=json.loads((OUT/'measurement_audit.json').read_text());assert audit['passed']
    summary=pd.read_csv(OUT/'accuracy_summary.csv')
    bins=pd.read_csv(OUT/'foreground_bins.csv')
    support=pd.read_csv(OUT/'common_support.csv')
    pairs=pd.read_csv(OUT/'pair_measurements.csv')
    primary_done='completion_primary' in audit['runs'];head_done='completion_head' in audit['runs']
    lines=['# Occlusion, visible animal area, and model performance','',
           'Updated November 10, 2026. Frozen AIMv2 and DINOv2 on Oxford-IIIT Pet. This report is generated from saved, audited predictions.','',
           '## Status','',
           f'- Foreground-conditioned reanalysis of existing results: complete.\n- 50%/75% primary-cohort extension: {"complete" if primary_done else "not yet included; inference in progress or awaiting audit"}.\n- Previously unused 185-image annotated cohort: {"complete" if head_done else "not yet included; preparation complete, inference/audit pending"}.',
           '- The encoders, clean-trained classifiers, mean pooling, and original results are unchanged.','',
           '## Question','',
           'How does model performance depend on the masking pattern, the amount of animal foreground that remains visible, and the animal regions retained? Image visibility and animal visibility use different denominators. Equal image visibility does not guarantee equal animal coverage, and equal animal coverage does not guarantee equal content.','',
           '## Accuracy across masking conditions','']
    if primary_done:
        def value(fraction,pattern,metric,fill=128):
            return summary[(summary.cohort=='primary')&(summary.fraction==fraction)&(summary.pattern==pattern)&(summary.metric==metric)&(summary.fill==fill)].iloc[0]
        gray=[value(f,'random','aim_minus_dino') for f in [.25,.5,.75]]
        black=value(.5,'random','aim_minus_dino',0)
        findings=['## Main findings','',
            f'- The center/random reversal depends on the visibility budget. With gray fill, the random-mask AIM-minus-DINO gap changes from {100*gray[0].estimate:+.1f} pp at 25% image visibility to {100*gray[1].estimate:+.1f} pp at 50%, then {100*gray[2].estimate:+.1f} pp at 75%. Center favors AIMv2 at all three budgets. These component signs are resolved by the prespecified approximate simultaneous intervals.',
            f'- At 75% image visibility, AIMv2 leads under both center and random masks with both fills. The original reversal therefore describes strong occlusion conditions, not a universal split between the models.',
            f'- Fill color matters near the transition. At 50% visibility with black random masks, the gap is {100*black.estimate:+.1f} pp, with simultaneous interval [{100*black.familywise_ci_low:+.1f}, {100*black.familywise_ci_high:+.1f}]. This does not resolve a winner, whereas the gray-fill contrast favors DINOv2.',
            '- Foreground-conditioned curves have limited overlap. Their remaining pattern differences are descriptive associations; sharing a visibility bin does not hold image identity or visible content fixed.','']
        position=lines.index('## Accuracy across masking conditions');lines[position:position]=findings
    if head_done:
        new=pairs[(pairs.cohort=='new_head')&(pairs.pair_type=='head_contrast')&(pairs.fill==128)].set_index('model')
        r=new.loc['aimv2'];d=new.loc['dinov2']
        findings=['### Check on previously unused images','',
            'The 185-image annotated cohort again resolves the center/random reversal at 25% image visibility with both fills. At 75%, both center and random point estimates favor AIMv2, but the random-mask simultaneous intervals include zero for both fills. The new cohort is consistent with the primary direction; it does not independently resolve the full 75% ordering. At 50%, the random-mask simultaneous intervals also include zero.',
            f'Among {int(r.n_images)} eligible new head pairs, mean animal visibility is {r.object_visibility_a:.1%} versus {r.object_visibility_b:.1%}, while mean head coverage is {r.head_visibility_a:.1%} versus {r.head_visibility_b:.1%}. Gray-fill accuracy is {r.accuracy_a:.1%} versus {r.accuracy_b:.1%} for AIMv2, and {d.accuracy_a:.1%} versus {d.accuracy_b:.1%} for DINOv2. The corresponding content-bundle gaps are {100*r.difference:.1f} and {100*d.difference:.1f} pp. These retain the earlier direction, with smaller gaps; other animal regions change alongside the head.','']
        position=lines.index('## Accuracy across masking conditions');lines[position:position]=findings
    for cohort in summary.cohort.unique():
        lines.extend([f'### {cohort}',''])
        clean=summary[(summary.cohort==cohort)&(summary.pattern=='clean')].set_index('metric')
        lines.extend([f'Clean-image accuracy: AIMv2 {clean.loc["aimv2","estimate"]:.1%}; DINOv2 {clean.loc["dinov2","estimate"]:.1%}. The tables compare absolute accuracy under occlusion, not a clean-normalized robustness score. The clean baselines already differ.',''])
        rows=[]
        for (fraction,fill,pattern),g in summary[(summary.cohort==cohort)&(summary.pattern!='clean')].groupby(['fraction','fill','pattern']):
            q=g.set_index('metric');d=q.loc['aim_minus_dino']
            rows.append([f'{fraction:.0%}', 'Gray' if fill==128 else 'Black',pattern,
                         f'{q.loc["aimv2","estimate"]:.1%}',f'{q.loc["dinov2","estimate"]:.1%}',
                         f'{100*d.estimate:+.1f} [{100*d.ci_low:+.1f}, {100*d.ci_high:+.1f}]',
                         f'{d.foreground_mean:.1%}',int(d.n_images)])
        lines.extend([table(rows,['Image visible','Fill','Pattern','AIMv2','DINOv2','AIM minus DINO, pp [95% CI]','Mean animal visible','Images']),'',
                      f'![Model ordering](../results/occlusion_completion/figures/{cohort}_model_ordering.png)',''])
    lines.extend(['The intervals above are paired, pointwise image-bootstrap intervals. Random-mask repeats are averaged within each original image. `accuracy_summary.csv` also reports approximate simultaneous intervals for the 12 center/random model-gap contrasts within each cohort. The two cohorts are not pooled.','',
                  '### Where the center/random ordering reverses',''])
    rows=[]
    for (cohort,fraction,fill),g in summary[(summary.metric=='aim_minus_dino')&summary.pattern.isin(['center','random'])].groupby(['cohort','fraction','fill']):
        t=g.set_index('pattern');c=t.loc['center'];r=t.loc['random']
        opposite=c.estimate*r.estimate<0
        supported=(c.familywise_ci_low*c.familywise_ci_high > 0 and r.familywise_ci_low*r.familywise_ci_high > 0)
        rows.append([cohort,f'{fraction:.0%}','Gray' if fill==128 else 'Black',f'{100*c.estimate:+.1f}',f'{100*r.estimate:+.1f}',
                     'Yes' if opposite else 'No','Yes' if supported else 'No'])
    lines.extend([table(rows,['Cohort','Image visible','Fill','Center gap (pp)','Random gap (pp)','Opposite point-estimate signs','Both signs resolved by simultaneous intervals']),'',
                  'The last column asks whether each gap has a definite sign, regardless of whether those signs agree. The intervals cover the 12 center and random comparisons within a cohort.','',
                  '## Foreground-conditioned accuracy','',
                  'Each panel holds image visibility, fill, and masking pattern fixed. The horizontal axis measures the fraction of the photographed animal that remains visible. The vertical axis is breed-classification accuracy. Curves describe different image groups; moving along a curve is not an intervention that reveals more of the same animal.',''])
    for cohort in summary.cohort.unique():
        for fraction in sorted(summary[(summary.cohort==cohort)&(summary.pattern!='clean')].fraction.unique()):
            lines.extend([f'![{cohort}, {fraction:.0%} image visibility, gray](../results/occlusion_completion/figures/{cohort}_foreground_{int(fraction*100)}_fill128.png)','',f'[Black-fill version](../results/occlusion_completion/figures/{cohort}_foreground_{int(fraction*100)}_fill0.png)',''])
    lines.extend(['Counts below each panel are original images, not the number of mask repetitions. Hollow points have 5–19 images; estimates with fewer than five are suppressed. Empty regions are not extrapolated. Intervals are pointwise; an all-correct sparse cell can have a degenerate empirical bootstrap interval, which does not establish certainty about unseen images.','',
                  'Main bins average random-mask coverage and correctness within image before binning. The saved `individual_repeats` sensitivity table instead bins each mask, gives each repeat weight 1/3, and retains image-level bootstrap clustering. The two conventions answer slightly different conditional questions.','',
                  '## Overlap limits the pattern comparison',''])
    rows=[]
    for r in support[(support.metric=='aim_minus_dino')&(support.fill==128)].itertuples():
        rows.append([r.cohort,f'{r.fraction:.0%}',f'{r.bin_width:.0%}',r.pattern,('None' if pd.isna(r.common_bins) else str(r.common_bins)),f'{r.n_retained}/{r.n_total}',
                     'Not estimable' if pd.isna(r.standardized_accuracy) else f'{r.standardized_accuracy*100:+.1f}'])
    lines.extend([table(rows,['Cohort','Image visible','Bin width','Pattern','Common bin indices (from zero)','Retained images','Standardized model gap (pp)']),'',
                  'These descriptive summaries use the same foreground-bin weights for all four patterns, proportional to the minimum count across patterns. They restrict the population, do not match image identity, and do not eliminate within-bin visibility or composition differences. No causal or uncertainty-based claim is made from these standardized point estimates.',''])
    t=bins[(bins.cohort=='primary')&(bins.fraction==.25)&(bins.fill==128)&(bins.bin_width==.2)&(bins.convention=='image_average')&(bins.fg_bin==1)&(bins.metric=='aimv2')].set_index('pattern')
    lines.extend([f'For example, in the original 20–40% foreground bin, center has {int(t.loc["center","n_images"])} images with mean foreground visibility {t.loc["center","foreground_mean"]:.1%}; random has {int(t.loc["random","n_images"])} images with mean {t.loc["random","foreground_mean"]:.1%}. A shared broad-bin label is not exact matching. Ten-point bins are reported as a prespecified sensitivity analysis, not chosen to obtain a desired ordering.','',
                  '## Retained animal regions',''])
    rows=[]
    for r in pairs[(pairs.pair_type=='head_contrast')&(pairs.fill==128)].itertuples():
        rows.append([r.cohort,r.model,int(r.n_images),f'{r.object_visibility_a:.1%} / {r.object_visibility_b:.1%}',
                     f'{r.head_visibility_a:.1%} / {r.head_visibility_b:.1%}',f'{r.body_visibility_a:.1%} / {r.body_visibility_b:.1%}',
                     f'{r.background_visibility_a:.1%} / {r.background_visibility_b:.1%}',f'{r.accuracy_a:.1%} / {r.accuracy_b:.1%}',
                     f'{r.difference*100:.1f} [{r.difference_low*100:.1f}, {r.difference_high*100:.1f}]'])
    lines.extend([table(rows,['Cohort','Model','Pairs','Animal visible','Head ROI visible','Other animal visible','Background visible','Accuracy','Accuracy gap, pp [95% CI]']),'',
                  'Values before/after the slash correspond to higher/lower head coverage. Region percentages are image averages; paired accuracy estimates weight represented breeds equally, matching the original head-pair analysis. Each visibility percentage uses its own original region as the denominator: head and other-animal visibility are not shares that add to 100%. Head ROI is the annotated head box intersected with animal foreground. “Other animal” is its complement, not a precise body-part segmentation.',''])
    for cohort in ['auxiliary_head','new_head']:
        if (pairs.cohort==cohort).any():
            lines.extend([f'![{cohort} region comparison](../results/occlusion_completion/figures/{cohort}_region_bundle.png)','',
                          f'![Actual {cohort} pairs](../results/occlusion_completion/figures/{cohort}_actual_pairs.png)',''])
    lines.extend(['The matched foreground rule applies to every selected pair, within three percentage points. It does not fix which pixels, textures, or background regions remain. Higher head coverage exchanges visible head-region pixels for other animal pixels. These results characterize a changed content bundle; they do not isolate a causal head effect or explain the main center/random comparison by themselves.',''])
    if head_done:
        prep=json.loads((ROOT/'results/completion_head/preparation_audit.json').read_text())
        lines.extend([f'The new cohort contains all 185 independently selected annotated images for standard-pattern evaluation, including those ineligible for a head pair. {prep["eligible_head_pairs"]} of 185 satisfy the unchanged pair rule. The cohort comes from unused official trainval images because the downloaded official test split lacks head-box XMLs. It is disjoint from prior training, validation, and evaluation IDs and exact image hashes. This is a new-image scope check with a different source split, not an identical-population replication.','',
                      '![Retained regions across standard masking patterns](../results/occlusion_completion/figures/new_head_standard_regions.png)','',
                      'One new-cohort image has no foreground outside its head box. Its other-animal visibility is undefined, rather than zero; the standard-region table reports the measurement count for every region. All 185 images remain in standard accuracy evaluation.','',
                      '`head_thirds.csv` reports head-coverage thirds within foreground bin, pattern, budget, and fill. Only seven of the twelve pattern-by-budget groups contain any foreground bin with at least two head thirds supported by five or more images each. These are still different image groups within broad intervals. Sparse cells are suppressed; missing cells cannot be used to establish an independent head effect.',''])
    lines.extend(['## What can be concluded','',
                  '- Report robustness for explicit masking conditions, not as a universal ordering of pretrained models.','- Report foreground visibility alongside the image mask budget: the same image budget can retain very different amounts of animal.','- Foreground-area conditioning must show overlap and sample sizes. Residual pattern differences are associations under this evaluation, not proof of a pure position or training effect.','- Describe retained region bundles explicitly. Similar foreground area does not hold semantic content fixed.','',
                  'The frozen classifiers, pooling, synthetic fill masks, one fine-grained dataset, annotation proxies, and different pretraining histories limit generalization. The primary extension reuses previously analyzed images. The new head cohort is separately reported. No pooling ablation, internal mechanism claim, or improved breed classifier is part of this study.','',
                  '## Relation to earlier work','',
                  '[Naseer et al., Intriguing Properties of Vision Transformers](https://arxiv.org/html/2105.10497v3) study transformer robustness using random, salient, and non-salient patch occlusions. Occlusion evaluation itself is therefore established; this project contributes a bounded comparison of two later fixed encoder/probe systems with explicit foreground measurements and overlap checks.','',
                  '[Kassaw et al., Image Recognition Under Occlusion](https://arxiv.org/html/2409.10775v1) evaluate real and synthetic occlusion and discuss diffuse occlusion. Their work motivates checking more than one occlusion condition. This project uses artificial pixel fills on Pet images and does not establish performance under real occluders.','',
                  '## Reproduction and checks','',
                  'Use the decoder-pinned reference environment from the repository. The completion runner refuses changed preparation locks, replays eight original conditions per model, verifies transformed-input fingerprints, binds caches to models/classifiers/configuration, and reconstructs predictions from saved features. The analysis independently reproduces the previous headline scores and validates one-to-one shared-condition joins.','',
                  '```bash\nsource scripts/env.sh\n.reference-conda/bin/python scripts/complete_occlusion.py prepare --cohort primary\n.reference-conda/bin/python scripts/complete_occlusion.py prepare --cohort head\n# For each cohort and each model, run and audit as in scripts/run_completion.sh.\nOPENBLAS_NUM_THREADS=4 .reference-conda/bin/python scripts/analyze_completion.py\n.reference-conda/bin/python scripts/completion_examples.py\n.reference-conda/bin/python scripts/verify_completion.py\n.reference-conda/bin/python scripts/report_completion.py\n```','',
                  'The fixed design is in `docs/OCCLUSION_COMPLETION_PROTOCOL.md`; stage planning is in `docs/OCCLUSION_COMPLETION_PLAN.md`. Source tables and figures are under `results/occlusion_completion/`. Codex assisted protocol implementation, execution, analysis, and documentation under the existing AI-use disclosure.'])
    if (ROOT/'results/patch_relocation/summary.csv').exists():
        extra = final_comparisons()
        if (ROOT/'results/region_swap/summary.csv').exists():
            extra.extend(region_results())
        lines[lines.index('## Accuracy across masking conditions'):lines.index('## Accuracy across masking conditions')] = extra
    (ROOT/'reports/OCCLUSION_COMPLETION_EN.md').write_text('\n'.join(lines)+'\n')
    print('Saved reports/OCCLUSION_COMPLETION_EN.md')


def final_comparisons():
    loss = pd.read_csv(OUT/'clean_loss.csv')
    matched = pd.read_csv(OUT/'area_matched_patterns.csv')
    relocated = pd.read_csv(ROOT/'results/patch_relocation/summary.csv')
    example = loss.query("cohort=='primary' and fraction==.75 and fill==128 and pattern=='random'").iloc[0]
    held = loss.query("cohort=='new_head' and fraction==.75 and fill==128 and pattern=='random'").iloc[0]
    section = ['## Clean accuracy changes the interpretation', '',
               'Each original image contributes its clean correctness minus its average masked correctness. A positive loss means fewer correct breed predictions after masking. The gap in losses subtracts the DINOv2 loss from the AIMv2 loss. Both models see the same images and random masks.', '']
    rows = []
    for name in ['aimv2','dinov2']:
        rows.append([name, f'{example[name+"_clean"]:.1%}',f'{example[name+"_masked"]:.1%}',
                     f'{100*example[name+"_loss"]:.1f}',f'{example[name+"_joint_retained"]:.1%}'])
    section += ['Gray random masking with 75% image visibility on the main 740 images.', '',
                table(rows,['Model','Clean accuracy','Masked accuracy','Net loss (pp)','Accuracy among images both classified correctly when clean']), '',
                f'AIMv2 finishes with higher accuracy and loses {100*example.loss_gap:.1f} pp more from its clean baseline (adjusted 95% interval {100*example.family_low:.1f} to {100*example.family_high:.1f} pp). On the {int(example.n_joint_clean_correct)} images both models originally got right, their retained accuracies are close. This subset excludes initial errors, so it answers a different question from the full-sample net loss.', '',
                f'The corresponding loss difference on the 185 annotated images is {100*held.loss_gap:.1f} pp (adjusted interval {100*held.family_low:.1f} to {100*held.family_high:.1f} pp). The follow-up comparisons are exploratory. [All 48 conditions](../results/occlusion_completion/clean_loss.csv) and [analysis rules](../docs/FINAL_SENSITIVITY.md).', '',
                '## Moving visible patches at matched animal area','']
    counts = matched.query("cohort=='primary' and fill==128").sort_values('fraction').eligible.astype(str).tolist()
    section += [f'Of the 740 main images, only {", ".join(counts)} respectively had an existing uniform random mask within three percentage points of the center mask at 25%, 50%, and 75% image visibility. The design required at least 20 for a subset estimate. [Pair counts and support](../results/occlusion_completion/area_matched_patterns.csv).', '',
                'We then generated two new masks per eligible image. Starting from the 25% center condition, each new mask keeps the same number of patches in each animal-coverage band, moves at least 16 of 64 patches, and preserves the fraction of animal visible within three percentage points. We scored both masks and a center replay with gray fill. These annotation-guided masks represent a different intervention from uniform random patches.', '']
    rows = []
    for cohort,g in relocated.groupby('cohort',sort=False):
        for r in g.itertuples():
            rows.append([cohort,r.metric,f'{r.eligible}/{r.total}',f'{r.center_acc:.1%}' if pd.notna(r.center_acc) else '—',
                         f'{r.relocated_acc:.1%}' if pd.notna(r.relocated_acc) else '—',
                         f'{100*r.center_minus_relocated:+.1f}',f'[{100*r.family_low:+.1f}, {100*r.family_high:+.1f}]'])
    section += [table(rows,['Cohort','Measure','Eligible','Center','Relocated','Difference (pp)','Adjusted 95% interval (pp)']), '',
                'For each model, difference is center accuracy minus relocated accuracy. Interaction is the AIMv2 difference minus the DINOv2 difference. Intervals use paired original images and adjust for these three comparisons within each cohort.', '']
    for cohort,g in relocated.groupby('cohort',sort=False):
        r=g.iloc[0]
        section.append(f'In the {cohort} cohort, mean animal visibility is {r.center_animal:.1%} for center and {r.relocated_animal:.1%} after relocation. The relocated versions exchange an average of {r.mean_exchanged:.1f} of the 64 visible patches.')
    main = relocated[relocated.cohort.eq('primary')].set_index('metric')
    repeat = relocated[relocated.cohort.eq('new_head')].set_index('metric')
    section += ['', f"On the main images, moving the patches reduces AIMv2 accuracy by {100*main.loc['aimv2','center_minus_relocated']:.1f} pp and increases DINOv2 accuracy by {-100*main.loc['dinov2','center_minus_relocated']:.1f} pp. The difference in responses is {100*main.loc['interaction','center_minus_relocated']:.1f} pp (adjusted 95% interval {100*main.loc['interaction','family_low']:.1f} to {100*main.loc['interaction','family_high']:.1f}). The annotated cohort shows the same directions, with a difference in responses of {100*repeat.loc['interaction','center_minus_relocated']:.1f} pp."]
    section += ['', 'The comparison measures sensitivity to this change in visible content and arrangement at closely matched animal area. Patch adjacency, texture, animal parts and background pixels can change together. Both cohorts have appeared in earlier experiments. [Design and execution](../docs/PATCH_RELOCATION.md) and [full results](../results/patch_relocation/summary.csv).', '']
    return section


def region_results():
    folder=ROOT/'results/region_swap'
    design=pd.read_csv(folder/'candidates.csv')
    scores=pd.read_csv(folder/'summary.csv').set_index(['suite','model','metric'])
    n=int(design.regional.sum()); eligible=int(design.regional_eligible.sum())
    direct=int(design.direct_eligible.eq(True).sum())
    overlap=int((design.regional & design.direct_eligible.eq(True)).sum())
    section=['## Two tests on fresh official test photos','',
             f'All previous project image IDs and exact JPEG hashes were excluded before selecting these photos. The direct replication sampled ten new images per breed. Of 370 sampled, {direct} supported the original relocation rule. The regional experiment required four visible and four hidden pure patches in each of animal and background. {eligible} of {int(design.reason.eq("valid").sum())} candidate photos qualified. Up to ten per breed gave {n} regional photos. The samples share {overlap} images. Estimates give equal weight to each of the 37 breeds.','',
             'The direct replication used the previous design, with two fixed relocations per eligible image. Differences below use center accuracy minus relocated accuracy. Each interval adjusts for the two models within this comparison.','']
    rows=[]
    for m in ['aimv2','dinov2']:
        c=scores.loc['direct',m]; d=c.loc['center_cost']
        rows.append([m,f'{c.loc["center","estimate"]:.1%}',f'{c.loc["relocated","estimate"]:.1%}',f'{d.estimate*100:+.1f}',f'[{d.adjusted_low*100:+.1f}, {d.adjusted_high*100:+.1f}]'])
    section.extend([table(rows,['Model','Center','Relocated','Center minus relocated (pp)','Adjusted 95% interval (pp)']),'',
                    'For the regional experiment, each single-region change hides four visible patches and reveals four others from the same region. The original pixels keep their positions. Other regions, mixed patches, fill color, image budget and the exact visible pixel counts of each trimap class are fixed. The combined condition applies both exchanges.',''])
    rows=[]
    for m in ['aimv2','dinov2']:
        c=scores.loc['regional',m]; d=c.loc['animal_minus_background_cost']
        rows.append([m,*[f'{c.loc[k,"estimate"]:.1%}' for k in ['center','animal','background','both']],
                     f'{100*d.estimate:+.1f}',f'[{100*d.adjusted_low:+.1f}, {100*d.adjusted_high:+.1f}]'])
    section.extend([table(rows,['Model','Center','Animal swap','Background swap','Both swaps','Animal minus background cost (pp)','Adjusted 95% interval (pp)']),'',
                    'Each regional cost averages the change from applying its swap at both settings of the other region. The difference between costs reduces to background-only accuracy minus animal-only accuracy. A positive difference means the animal exchange cost more accuracy. A negative difference means it cost less. A range spanning zero leaves the ordering uncertain. The full table includes both costs, the factorial interaction and pointwise intervals.','',
                    'Only photos with enough pure animal and background patches near and outside the center support this experiment. It tests small exchanges, with one regional draw per photo. It does not recover causal contributions to the larger relocation or identify a pretraining mechanism. Prior research has already separated foreground and background cues in recognition. The contribution here is the paired, equal-size intervention in the two fixed Pet classifiers and its comparison with the earlier behavior. [Xiao et al.](https://openreview.net/pdf?id=gl3D-xY7wLq), [locked design](../docs/REGION_SWAP_PROTOCOL.md), [estimates and intervals](../results/region_swap/summary.csv).',''])
    for m,label in [('aimv2','AIMv2'),('dinov2','DINOv2')]:
        d=scores.loc['regional',m,'animal_minus_background_cost']
        gain=-100*d.estimate
        lower,upper=-100*d.adjusted_high,-100*d.adjusted_low
        section.append(f'{label} accuracy after an animal-only exchange minus accuracy after a background-only exchange was {gain:+.1f} pp (adjusted interval {lower:+.1f} to {upper:+.1f}).')
    section += ['', 'DINOv2 gained more accuracy when the exchange involved animal patches. AIMv2 showed no resolved difference between the two exchange locations. This locates a behavioral difference under an exact area constraint. Within each region the particular texture, part and position can still change.', '']
    return section


if __name__=='__main__':main()
