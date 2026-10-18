import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

// Copy this script into .build-presentation/ before running, where node_modules
// links to the Codex bundled runtime. Scientific experiment reproduction does
// not depend on this presentation-authoring package.
const ROOT = process.cwd();
const SKILL = process.env.PRESENTATION_SKILL_DIR ?? '/Users/boshenyang/.codex/plugins/cache/openai-primary-runtime/presentations/26.1017.11052/skills/presentations';
const RUNTIME_PYTHON = process.env.PRESENTATION_PYTHON ?? '/Users/boshenyang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const data = JSON.parse(await fs.readFile(path.join(ROOT, 'milestone/slide_data.json'), 'utf8'));
if (data.audit.completed_prediction_models.length !== 2) throw new Error('Both models must finish and pass the integration audit.');
const pres = Presentation.create({slideSize:{width:1280,height:720}});
const FONT = 'Arial', INK='#17313D', TEAL='#007F7B', GRAY='#52616A';
const pct = n => `${(n*100).toFixed(1)}%`;
const pp = n => (n*100).toFixed(1);
const get = (m,p,f) => data.summary.find(r=>r.model===m&&r.pattern===p&&r.fraction===f);
const pair = (m,p) => data.pairs.find(r=>r.model===m&&r.pair_type===p);
const notes = [];

function text(slide, value, x,y,w,h,size=27,color=INK,bold=false){
  const s=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  s.text=value;
  s.text.style={typeface:FONT,fontSize:size,color,bold,verticalAlignment:'top',insets:0,wrap:'square',autoFit:'none'};
  return s;
}
function slide(title, note, source='Saved pilot_v1 predictions, configuration and docs/PROTOCOL.md'){
  const s=pres.slides.add(); s.background.fill='#FFFFFF';
  const n=pres.slides.items.length;
  text(s,title,64,43,1150,104,44,INK,true);
  text(s,String(n).padStart(2,'0'),1190,680,45,20,14,GRAY);
  s.speakerNotes.text=`${note}\n\nSOURCES: ${source}`;
  notes.push({slide:n,title,note,source});
  return s;
}
function image(s,file,x=64,y=175,w=1152,h=425,alt=file){
  s.images.add({path:path.join(ROOT,'milestone/assets',file),position:{left:x,top:y,width:w,height:h},fit:'contain',alt});
}
function table(s,values,x,y,w,h,widths){
  const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});
  t.borders.assign({style:'solid',fill:'#D8E1E4',width:.5});
  for(let r=0;r<values.length;r++) for(let c=0;c<values[0].length;c++){
    const cell=t.getCell(r,c); cell.fill=r===0?'#E9F4F3':'#FFFFFF';
    cell.text.style={typeface:FONT,fontSize:23,color:r===0?TEAL:INK,bold:r===0,verticalAlignment:'middle'};
  }
  return t;
}

{
 const s=pres.slides.add(); s.background.fill='#F7FAFA';
 text(s,'COMP 669 PROJECT MILESTONE',64,76,1000,36,18,TEAL,true);
 text(s,'What does occlusion\nrobustness measure?',64,172,1130,190,64,INK,true);
 text(s,'Separating visible image area from visible foreground\nin frozen AIMv2 and DINOv2',68,393,1100,100,32,GRAY);
 text(s,'Boshen Yang\nOxford-IIIT Pet pilot, executed October 18, 2026',68,586,1100,66,23,GRAY);
 const note='My original proposal asked how AIMv2 and DINOv2 degrade when less of an image is visible. After the feedback, I narrowed the question. The important issue is not simply that occlusion reduces accuracy. It is what the experiment actually removes, and what its results let us conclude. This milestone uses a small, real experiment with foreground annotations. I will show the inputs, the results, and the limits of the comparison. The model encoders stay frozen throughout.';
 s.speakerNotes.text=note;notes.push({slide:1,title:'What does occlusion robustness measure?',note,source:'docs/PROTOCOL.md'});
}
{
 const s=slide('Equal image area can retain unequal foreground',
 'Suppose two masks both keep half the image. One may retain almost the entire animal, while the other keeps mostly the background. In that case, a difference between the masks is hard to interpret as a location preference. This is the motivation for recording foreground visibility separately. The foreground mask describes the visible animal in the original photograph. It does not tell us which parts are most useful for identifying its breed, so area matching will still have limits. This project examines how much these distinctions matter for interpreting our model evaluation.',
 'Oxford-IIIT Pet trimap annotations; docs/PROTOCOL.md; Naseer et al., https://arxiv.org/abs/2105.10497');
 text(s,'Image visibility',64,181,520,47,28,TEAL,true);
 text(s,'How much of the whole image remains?',64,240,520,110,34);
 text(s,'Foreground visibility',675,181,520,47,28,TEAL,true);
 text(s,'How much of the annotated animal remains?',675,240,520,110,34);
 text(s,'The original comparison mixes image area, object content and spatial position.',64,451,1110,110,36,INK,true);
 text(s,'Foreground area is a measurable proxy. It is not the same as semantic information.',64,590,1120,61,23,GRAY);
}
{
 const s=slide('The revised question is about interpretation',
 'I ask whether mask-location differences persist after accounting for visible foreground. I first measure how much foreground each standard mask keeps. Then I construct same-image pairs with the same square occluder size. Some pairs retain very different foreground amounts. Other pairs retain almost the same amount but place the occluder elsewhere. AIMv2 is the primary model, and DINOv2 is a reference model under the same inputs. Prior PatchDrop work already distinguishes salient foreground and non-salient background. My contribution is a reproducible extension using pixel annotations and explicit matched-pair diagnostics, rather than claiming that foreground and background effects are new.',
 'Naseer et al., https://arxiv.org/html/2105.10497v3, Sec. 3.1; Xiao et al., https://arxiv.org/abs/2006.09994; docs/RELATED_WORK.md');
 text(s,'Do mask-location differences remain\nwhen visible foreground is similar?',64,171,1120,120,39,INK,true);
 text(s,'1. Measure foreground coverage under each mask.\n\n2. Compare equal-area, same-image diagnostic pairs.\n\n3. Characterize both encoders under shared conditions.',64,337,1110,230,29);
 text(s,'Scope: a replication and extension of prior occlusion work.',64,612,1120,43,23,GRAY);
}
{
 const s=slide('The pilot uses frozen encoders and clean probes',
 'I changed the pilot dataset from ImageNet-100 to Oxford-IIIT Pet because it provides pixel-level foreground labels. This is a breed-classification experiment across 37 categories. I use the official split, with 40 training images, 10 validation images and 5 official-test images per class. Fourteen images with empty foreground annotations were excluded before sampling. The encoders remain frozen. Each model has its own logistic classifier trained only on clean training features. Clean validation chooses the regularization parameter. The test labels do not choose that parameter, the masks, or the matching threshold. Both models use mean final patch features and the same preprocessing, which is a diagnostic recipe rather than their published best evaluation setup.');
 table(s,[['Setting','Pilot choice'],['Data','Oxford-IIIT Pet, 37 breed classes'],['Split','1,480 train / 370 validation / 185 test'],['Encoders','Frozen AIMv2-L/14 and DINOv2-L/14'],['Probe','Mean patch features, L2 norm, logistic classifier'],['Selection','Clean validation chooses C; no test tuning'],['Input','Full-frame 224x224; hidden RGB pixels = 128']],64,166,1152,412,[250,902]);
 text(s,'Only 5 test images per breed. All results are preliminary.',64,614,1120,40,24,GRAY);
}
{
 const s=slide('Both models receive these same masked pixels',
 'These are actual inputs from one of the held-out images, rather than schematic masks. Across the row, image visibility decreases from 100 percent to 25 percent. The second line records the fraction of annotated foreground that remains. I resize the full image and the annotation together before applying the mask. Hidden pixels receive a gray value of 128 before normalization. There is no crop or resize after masking. I keep every patch token, and I do not call either model\'s native mask interface. This makes the intervention a shared pixel-level occlusion test. It also means the experiment does not save inference compute.');
 image(s,'ratios_inputs.png',64,176,1152,345,'Same held-out image at 100, 75, 50 and 25 percent visible image area');
 text(s,'Also tested: suffix, center-nearest and 3 fixed random repetitions.',64,553,1120,40,27);
 text(s,'Exact patch budgets. All tokens remain. Gray fill precedes normalization.',64,613,1120,40,23,GRAY);
}
{
 const ac=get('aimv2','clean',1), dc=get('dinov2','clean',1);
 const s=slide('Initial accuracy curves depend on the mask',
 `The clean held-out accuracies are ${pct(ac.accuracy)} for AIMv2 and ${pct(dc.accuracy)} for DINOv2 under this shared probe recipe. These panels show accuracy as image visibility changes. The shaded intervals resample original test images. For random masks, the three repetitions are averaged within each image first. The curves characterize these checkpoints and this dataset. Even if one model is higher in a panel, that does not identify which aspect of its pretraining caused the difference. Before interpreting a mask as easy or difficult, I next check how much foreground it keeps.`,
 'results/pilot_v1/summary.csv and paired_model_differences.csv; 2000 original-image bootstrap resamples');
 image(s,'accuracy_curves.png',95,151,1090,475,'Four mask-specific accuracy curves with image-bootstrap confidence intervals');
 text(s,`Clean accuracy: AIMv2 ${pct(ac.accuracy)} / DINOv2 ${pct(dc.accuracy)}. 185 test images.`,64,642,1140,31,22,GRAY);
}
{
 const c=get('aimv2','center',.5),r=get('aimv2','random',.5);
 const s=slide('At 50% image visibility, foreground coverage varies',
 `These distributions come from the input masks and annotations, so they are identical for the two models. At 50 percent visible image area, center-nearest masks retain an average ${pct(c.mean_object_visibility)} of the annotated foreground, compared with ${pct(r.mean_object_visibility)} for the random condition. This explains why image visibility alone is an incomplete description of the test. It does not prove that foreground area fully explains an accuracy difference. For example, a small visible face could matter more than a larger patch of fur. The matched-pair experiment is a first diagnostic step toward separating some of these conditions.`,
 'results/pilot_v1/conditions.csv and summary.csv; foreground label 1 only; unknown trimap label 3 excluded');
 image(s,'foreground_coverage.png',110,172,1060,375,'Foreground coverage distributions under equal visible image area');
 text(s,`Center mean: ${pct(c.mean_object_visibility)}     Random mean: ${pct(r.mean_object_visibility)}`,64,572,1120,44,31,TEAL,true);
 text(s,'This is an input-composition finding, not a new general law of robustness.',64,636,1120,31,22,GRAY);
}
{
 const s=slide('Same-image pairs fix occluder area and shape',
 'Every example on this slide keeps 75 percent of the image and uses the same square occluder shape. I generate 25 possible placements on a fixed grid. The first pair chooses the placements that retain the most and least foreground. The second pair matches foreground visibility within three percentage points and requires separated occluder locations. The annotations choose the pairs before any model outputs are examined. All 185 test images have an eligible matched pair under this rule. This is an oracle diagnostic using annotations, not an annotation-free method for deployment. It controls image identity, shape and area, but it still changes which animal parts and which background pixels remain.');
 image(s,'pairs_inputs.png',64,174,1152,340,'Same-image object-contrast and foreground-visibility-matched diagnostic pairs');
 text(s,'Matched pair: foreground-visibility gap <= 3 percentage points.',64,548,1120,45,30,TEAL,true);
 text(s,'Selection uses annotations only. Equal foreground area can still expose different parts.',64,615,1120,48,23,GRAY);
}
{
 const a=pair('aimv2','object_contrast'),d=pair('dinov2','object_contrast');
 const am=pair('aimv2','visibility_matched'),dm=pair('dinov2','visibility_matched');
 const s=slide('Paired diagnostics quantify two different changes',
 `The upper table compares the same image with higher and lower foreground visibility while fixing square-occluder area and shape. AIMv2's paired difference is ${pp(a.paired_accuracy_difference)} percentage points, with a 95 percent interval from ${pp(a.difference_ci_low)} to ${pp(a.difference_ci_high)}. DINOv2's difference is ${pp(d.paired_accuracy_difference)} points, with an interval from ${pp(d.difference_ci_low)} to ${pp(d.difference_ci_high)}. The lower figures describe pairs whose foreground coverage is already close. Correctness changes for ${pct(am.correctness_discordance)} of AIMv2 pairs and ${pct(dm.correctness_discordance)} of DINOv2 pairs. These flips show why an average signed difference alone can hide changes. They do not establish a pure spatial effect.`,
 'results/pilot_v1/paired_summary.csv; paired image-bootstrap confidence intervals; n=185 per diagnostic');
 table(s,[['Model','More FG','Less FG','Paired difference (95% CI)'],['AIMv2',pct(a.accuracy_a),pct(a.accuracy_b),`${pp(a.paired_accuracy_difference)} pp [${pp(a.difference_ci_low)}, ${pp(a.difference_ci_high)}]`],['DINOv2',pct(d.accuracy_a),pct(d.accuracy_b),`${pp(d.paired_accuracy_difference)} pp [${pp(d.difference_ci_low)}, ${pp(d.difference_ci_high)}]`]],64,184,1152,180,[190,220,220,522]);
 text(s,'Within foreground-visibility-matched pairs',64,423,1120,42,30,TEAL,true);
 text(s,`Correct / wrong flips: AIMv2 ${pct(am.correctness_discordance)} / DINOv2 ${pct(dm.correctness_discordance)}`,64,484,1120,47,31);
 text(s,`Predicted class changes: AIMv2 ${pct(am.prediction_disagreement)} / DINOv2 ${pct(dm.prediction_disagreement)}`,64,549,1120,43,27);
 text(s,'All diagnostic occluders hide 25% of the image. n = 185 paired images.',64,636,1120,30,22,GRAY);
}
{
 const s=slide('Similar foreground area can retain different parts',
 'This is an illustrative case selected after the experiment, using a stored rule that prioritizes correctness changes and then large target-probability changes. It is not evidence for how common a pattern is; the previous slide reports the full test-set rates. The two occluded inputs have closely matched foreground area but expose different regions of the animal. The displayed probabilities are the probes\' probabilities of the correct breed. We can inspect the surviving parts as a possible explanation, but we have not measured head visibility on this test set. The downloaded head boxes cover only the official training subset. That limitation is why I describe this as a diagnostic case rather than a controlled part-level explanation.');
 image(s,'matched_case.png',64,173,1152,383,'Post-hoc illustrative matched-visibility pair with actual classifier outcomes');
 text(s,'Area matching does not match part identity, texture or background.',64,585,1120,46,30,TEAL,true);
 text(s,'Post-hoc illustration. Full-set rates come from the paired table.',64,642,1120,30,22,GRAY);
}
{
 const s=slide('What the pilot supports, and what remains open',
 'The pilot establishes an executable evaluation and real paired observations under a clearly specified pixel intervention. It lets us show that equal image-area masks retain different foreground coverage, and quantify how predictions change under two same-image diagnostic designs. Importantly, the four standard mask patterns have no eligible common coverage bin at 50 percent image visibility under the prespecified rule. I therefore cannot report a reliable adjusted four-pattern comparison there. The square-occluder pairs are a different diagnostic, not a solution to that missing overlap. Nothing here identifies the effect of prefix attention. The next priority is a larger test set, another fill color, and a design with better coverage overlap.');
 text(s,'Supported in this pilot',64,177,530,43,29,TEAL,true);
 text(s,'Shared-input model evaluation\n\nMeasured foreground coverage\n\nSame-image paired diagnostics',64,246,530,250,29);
 text(s,'Still open',681,177,530,43,29,TEAL,true);
 text(s,'No common bin at 50% image area\n\nPart-level and background effects\n\nMore data and another fill color',681,246,530,250,29);
 text(s,'Cross-model behavior does not identify a pretraining mechanism.',64,592,1140,56,31,INK,true);
}
{
 const s=slide('Code, next experiments and AI use',
 'The repository contains the protocol, source hashes, data manifests, model predictions, analysis code and figures. It is currently private, so I need to arrange instructor access before submitting the link. For the final project, I will prioritize a larger test set and fill-color sensitivity, then a more precise analysis of the content that remains visible. I used OpenAI Codex for literature inspection, implementation, debugging, execution and analysis drafting. The saved outputs provide the evidence for the reported numbers, and I need to review and understand the code and interpretations before presenting them. The main related works are PatchDrop, the backgrounds challenge, AIMv2, DINOv2 and the Oxford-IIIT Pet dataset.',
 'https://github.com/Bensssonxx/comp669-object-visibility; docs/AI_USE.md; docs/RELATED_WORK.md');
 text(s,'github.com/Bensssonxx/comp669-object-visibility',64,183,1152,60,30,TEAL,true);
 text(s,'Next: larger held-out test set, second fill color, part-level analysis.',64,280,1140,95,31);
 text(s,'AI use: Codex assisted source review, code, debugging, execution and analysis drafting.',64,402,1130,100,27);
 text(s,'References: PatchDrop (2021), Backgrounds Challenge (2020),\nAIMv2 (2024), DINOv2 (2023), Oxford-IIIT Pet (2012).',64,551,1130,80,24,GRAY);
}

const version=process.env.MILESTONE_VERSION ?? 'v1';
const build=path.join(ROOT,'.build-presentation',version);
const finalPath=path.join(ROOT,`milestone/COMP669_Object_Visibility_Milestone_${version}.pptx`);
await fs.mkdir(build,{recursive:true});
await fs.mkdir(path.join(build,'previews'),{recursive:true});
for(const [i,s] of pres.slides.items.entries()){
  const png=await pres.export({slide:s,format:'png',scale:1});
  await fs.writeFile(path.join(build,'previews',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(pres)).save(candidate);
await fs.writeFile(path.join(ROOT,'milestone/SPEAKER_NOTES_EN.md'),notes.map(n=>`## ${n.slide}. ${n.title}\n\n${n.note}\n\nSources: ${n.source}`).join('\n\n'));
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath,
 pythonExecutable:RUNTIME_PYTHON,
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 explicitTotalSlideCount:12,requiredNativeTableOwnerSlides:[4,9],requiredNativeChartOwnerSlides:[],
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','4','--require-native-table-slide','9'],
 fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,
 receiptPath:path.join(build,'validation.json')});
console.log(JSON.stringify({finalPath,result},null,2));
