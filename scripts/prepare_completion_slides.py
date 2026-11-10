"""Prepare final presentation evidence only after both new inference audits pass."""
import json,re,hashlib
from pathlib import Path
import pandas as pd
from PIL import Image
from occlusion_visibility.data import load_image
from occlusion_visibility.experiment import decode_mask
from occlusion_visibility.masks import apply_mask

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/occlusion_completion'


def main():
    audit=json.loads((OUT/'measurement_audit.json').read_text())
    assert audit['passed'] and set(audit['runs'])=={'extension_v2','completion_primary','completion_head'}
    assert json.loads((OUT/'verification.json').read_text())['passed']
    summary=pd.read_csv(OUT/'accuracy_summary.csv');bins=pd.read_csv(OUT/'foreground_bins.csv');pairs=pd.read_csv(OUT/'pair_measurements.csv')
    raw=pd.read_csv(OUT/'analysis_conditions.csv')
    def stat(cohort,fraction,pattern,model,fill=128):
        return float(summary[(summary.cohort==cohort)&(summary.fraction==fraction)&(summary.pattern==pattern)&(summary.metric==model)&(summary.fill==fill)].estimate.iloc[0])
    def pair(cohort,model):return pairs[(pairs.cohort==cohort)&(pairs.pair_type=='head_contrast')&(pairs.fill==128)&(pairs.model==model)].iloc[0]
    old=pair('auxiliary_head','aimv2');new=pair('new_head','aimv2')
    p=lambda x:f'{x*100:.1f} percent'
    sources=['docs/OCCLUSION_COMPLETION_PROTOCOL.md','results/occlusion_completion/accuracy_summary.csv','results/occlusion_completion/foreground_bins.csv','results/occlusion_completion/pair_measurements.csv','results/occlusion_completion/verification.json']
    sources += ['results/occlusion_completion/clean_loss.csv', 'results/occlusion_completion/area_matched_patterns.csv', 'results/patch_relocation/summary.csv', 'results/patch_relocation/conditions.csv']
    relocated=pd.read_csv(ROOT/'results/patch_relocation/summary.csv')
    main_pair=relocated.query("cohort=='primary'").set_index('metric')
    follow=relocated.query("cohort=='new_head'").set_index('metric')
    loss=pd.read_csv(OUT/'clean_loss.csv').query("cohort=='primary' and fraction==.75 and fill==128 and pattern=='random'").iloc[0]
    source='; '.join(sources)
    titles=['Comparing AIMv2 and DINOv2 Under Occlusion','Research question','Data and fixed evaluation setup',
            'Image visibility and animal visibility','The initial ranking reversal','Accuracy versus animal visibility',
            'Moving patches while matching animal area','Model ordering across visibility budgets','Similar animal area, different content',
            'A check on previously unused images','Head-region pairs on the new images','What this study tells us']
    notes=[
        "Hi everyone, I'm Boshen. My project studies occlusion robustness: how well image recognition works when some of the image is hidden. I compare AIMv2 and DINOv2 on cat and dog breeds. I focus on the testing conditions that make one model appear better than the other.",
        "A drop in accuracy after hiding information is expected. My question is more specific: does the masking pattern change which model performs better, and what animal content remains visible in those tests? This matters when we evaluate or choose a model. An accuracy score is easier to interpret when we know what evidence the model could actually see. I first explain the fixed setup, then show the inputs and results.",
        "I use Oxford-IIIT Pet, with thirty-seven breeds. The pretrained encoders stay frozen. Separate classifiers were trained using fourteen hundred eighty clean images, with three hundred seventy validation images for settings. The main evaluation uses seven hundred forty images. I also selected one hundred eighty-five previously unused images with head annotations. Both models receive identical masked pixels. The classifiers, pooling, and preprocessing stay fixed. The models still have different training histories, so this is a comparison of released systems, not a controlled training experiment.",
        "These two masked versions both keep twenty-five percent of the image. But the center version keeps about eighty-four percent of this animal, while the random version keeps about twenty-two percent. Image visibility counts all image pixels. Animal visibility counts only pixels labeled as animal foreground. Hidden pixels are filled with gray or black; patch tokens are not removed. This example explains why an equal image budget can produce very different recognition conditions.",
        f'On the main sample with gray fill and twenty-five percent image visibility, AIMv2 gets {p(stat("primary",.25,"center","aimv2"))} accuracy for center, versus {p(stat("primary",.25,"center","dinov2"))} for DINOv2. With random patches, the order reverses: {p(stat("primary",.25,"random","aimv2"))} versus {p(stat("primary",.25,"random","dinov2"))}. Black fill shows the same initial ordering. However, center and random retain different amounts of animal. Next, I look at accuracy against measured animal visibility.',
        "Here the horizontal axis is animal visibility, and the vertical axis is classification accuracy. Each panel holds the image budget and masking pattern fixed. The points summarize foreground-visibility intervals. Center covers a much wider range than random, which is concentrated near twenty-five percent. These are different image groups, so a line is not a causal experiment that reveals more of the same animal. The full report includes all four patterns, sample counts, and uncertainty intervals. That led me to compare two masks on the same photo.",
        f"Can we compare masks on the very same photo while keeping about the same amount of animal visible? Only eight of the original seven hundred forty photos had a random mask close enough at this budget. So I built two new masks per photo. I moved at least sixteen of the sixty-four visible patches and kept animal visibility within three percentage points of the center version. {int(main_pair.loc['aimv2','eligible'])} photos qualified. The table shows each model’s accuracy before and after moving the patches. AIMv2 went from {p(main_pair.loc['aimv2','center_acc'])} to {p(main_pair.loc['aimv2','relocated_acc'])}. DINOv2 went from {p(main_pair.loc['dinov2','center_acc'])} to {p(main_pair.loc['dinov2','relocated_acc'])}. The models respond in opposite directions. Which parts and textures they see can still change.",
        f"Now return to the original masks. At fifty percent visibility, gray random masks still favor DINOv2. Black random masks give no clear winner. At seventy-five percent, AIMv2 has higher accuracy under both patterns and both fills. But AIMv2 started higher on clean images. Under gray random masks, it loses {100*loss.aimv2_loss:.1f} points from its clean score, and DINOv2 loses {100*loss.dinov2_loss:.1f}. Which model finishes higher and which loses less are two different questions. What parts of the animal were actually visible?",
        f'This separate experiment moves an equal-sized square on the same picture, always leaving seventy-five percent of the image visible. Among the original eligible head pairs, average animal visibility is {p(old.object_visibility_a)} versus {p(old.object_visibility_b)}. Head visibility is {p(old.head_visibility_a)} versus {p(old.head_visibility_b)}. Each percentage uses its own original region as the denominator. The remaining animal region changes in the opposite direction. The experiment therefore compares different visible-content combinations. It cannot isolate the head alone. I then repeat the broader evaluation on previously unused annotated images.',
        "The new cohort has one hundred eighty-five images, five per breed. They were excluded from all earlier training, validation, and evaluation, and selected before predictions. At twenty-five percent visibility, center again favors AIMv2 and random favors DINOv2. At seventy-five percent, the point estimates favor AIMv2 under both patterns, but the random-mask intervals are still too wide to resolve a winner. The matched patch experiment also repeats the opposite responses on 182 eligible photos. These photos come from the training-and-validation source split, which includes head boxes. I keep them separate from the main sample.",
        f'On the new images, {int(new.n_images)} pairs satisfy the same foreground-matching and head-contrast rules. Their average animal visibility is {p(new.object_visibility_a)} versus {p(new.object_visibility_b)}, while head visibility is {p(new.head_visibility_a)} versus {p(new.head_visibility_b)}. Both models are more accurate with higher head coverage, by about fifteen percentage points for AIMv2 and seven for DINOv2. Other animal regions and background are shown as well. This checks the earlier content comparison on new pictures, but it keeps the same limitation: head coverage changes together with other information.',
        "If I were choosing a model, I would ask how much of the image is usually hidden and which parts stay visible. I would report both accuracy on those images and the change from clean accuracy. Here, those measures can favor different models. The patch and head comparisons show why knowing the visible area alone is insufficient. These findings concern two fixed systems and artificial masks on pet photos. I used Codex to help with code, experiments, analysis and presentation. The link takes you to the code and predictions. Thank you."
    ]
    asset_dir=ROOT/'final/assets';asset_dir.mkdir(parents=True,exist_ok=True)
    selected=json.loads((ROOT/'results/extension_v2/design_example_selection.json').read_text())
    asset_meta=[]
    for group,name in [('primary',selected['primary_image_id']),('head',selected['auxiliary_image_id'])]:
        rgb,_=load_image(ROOT,name);Image.fromarray(rgb).save(asset_dir/f'{group}_original.png')
        if group=='primary':
            rows=[raw[(raw.image_id==name)&(raw.pattern==pat)&(raw.fraction==.25)&(raw.fill==128)&(raw.repeat==0)].iloc[0] for pat in ['center','random']]
            labels=['center','random']
        else:
            rows=[raw[(raw.image_id==name)&(raw.pair_type=='head_contrast')&(raw.pair_role==role)&(raw.fill==128)].iloc[0] for role in ['high','low']];labels=['high','low']
        for label,r in zip(labels,rows):
            pixels=apply_mask(rgb,decode_mask(r.mask_hex,224,14),128);Image.fromarray(pixels).save(asset_dir/f'{group}_{label}.png')
            asset_meta.append(dict(group=group,label=label,image_id=name,condition_id=r.condition_id,animal=r.object_visibility,head=None if pd.isna(r.head_visibility) else r.head_visibility))
    conditions=pd.read_csv(ROOT/'results/patch_relocation/conditions.csv')
    name=sorted(conditions.loc[conditions.cohort.eq('primary'),'image_id'].unique())[0]
    rgb,_=load_image(ROOT,name)
    for role,tag in [(0,'center'),(1,'relocated')]:
        r=conditions[(conditions.image_id==name)&(conditions.role==role)].iloc[0]
        Image.fromarray(apply_mask(rgb,decode_mask(r.mask_hex,224,14),128)).save(asset_dir/f'relocation_{tag}.png')
        asset_meta.append(dict(group='relocation',label=tag,image_id=name,animal=r.animal_visible))
    slides=[dict(title=title,note=note,source=source,words=len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b",note))) for title,note in zip(titles,notes)]
    words=sum(s['words'] for s in slides)
    assert words/90*60+40<720,(words,'Script exceeds 12 minutes at 90 wpm + pauses')
    def records(df):return json.loads(df.to_json(orient='records'))
    data=dict(slides=slides,summary=records(summary),bins=records(bins),pairs=records(pairs),assets=asset_meta,relocation=records(relocated),clean_loss=loss.to_dict(),
              source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in sources},
              word_count=words,seconds_at_90wpm_plus_pauses=words/90*60+40)
    (ROOT/'final/slide_data.json').write_text(json.dumps(data,indent=2)+'\n')
    text=['# Final presentation speaker notes','',f'{words} spoken words. Estimated {words/90+40/60:.1f} minutes at 90 words/minute including 40 seconds of pauses; not a rehearsal.','']
    for i,s in enumerate(slides,1):text.extend([f'## {i}. {s["title"]}','',s['note'],'',f'Sources (not spoken): {s["source"]}',''])
    (ROOT/'final/SPEAKER_NOTES_EN.md').write_text('\n'.join(text))
    print(json.dumps({'slides':len(slides),'words':words,'seconds':data['seconds_at_90wpm_plus_pauses']}))


if __name__=='__main__':main()
