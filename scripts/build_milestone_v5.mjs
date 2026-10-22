import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {PresentationFile, FileBlob} from '@oai/artifact-tool';

// Run a copy in .build-presentation/, whose node_modules links to the bundled runtime.
const ROOT=process.cwd();
const SKILL='/Users/boshenyang/.codex/plugins/cache/openai-primary-runtime/presentations/26.1017.11052/skills/presentations';
const PYTHON='/Users/boshenyang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
process.env.RUNTIME_NODE_MODULES ??= '/Users/boshenyang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
process.env.RUNTIME_NODE ??= process.execPath;
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const data=JSON.parse(await fs.readFile(path.join(ROOT,'milestone/slide_data_v5.json'),'utf8'));
if(!data.audit.passed||!data.analysis_audit.passed) throw Error('Completed audited v2 evidence required.');
for(const [file,hash] of Object.entries(data.evidence_sha256)){
 if(crypto.createHash('sha256').update(await fs.readFile(path.join(ROOT,file))).digest('hex')!==hash) throw Error(`Evidence changed: ${file}`);
}
const source=path.join(ROOT,'milestone/COMP669_Object_Visibility_Milestone_v4.pptx');
const sourceHash=crypto.createHash('sha256').update(await fs.readFile(source)).digest('hex');
const p=await PresentationFile.importPptx(await FileBlob.load(source));
if(p.slides.items.length!==12||p.slides.items[0].frame.width!==1280||p.slides.items[0].frame.height!==720) throw Error('Unexpected source deck');
const build=path.join(ROOT,'.build-presentation',process.env.MILESTONE_BUILD ?? 'v5');
await fs.mkdir(path.join(build,'previews'),{recursive:true});
const before=await p.inspect({kind:'slide,textbox,image,table,chart,layout',maxChars:1000000});
await fs.writeFile(path.join(build,'source-inspection.ndjson'),before.ndjson);
const records=before.ndjson.split('\n').filter(Boolean).map(x=>JSON.parse(x));
// Preserve the source slides, their layout/master assignments and the original cover.
// Recompose only their explicitly owned content to fit the new research narrative.
const deletions=records.filter(r=>r.slideIndex>0&&['textbox','image','table','chart'].includes(r.kind)).map(r=>r.id);
p.delete(deletions);
const FONT='Arial',INK='#17313D',TEAL='#007F7B',GRAY='#52616A',AIM='#0072B2',DINO='#D55E00';
const P=n=>`${(Number(n)*100).toFixed(1)}%`, PP=n=>(Number(n)*100).toFixed(1);
const sign=n=>`${Number(n)>=0?'+':''}${PP(n)}`;
const stat=(model,fill,pattern)=>data.summary.find(r=>r.cohort==='primary'&&r.model===model&&Number(r.fill)===fill&&r.pattern===pattern);
const pair=(model,fill,type)=>data.pairs.find(r=>r.model===model&&Number(r.fill)===fill&&r.pair_type===type);
const contrast=(pattern,fill)=>data.contrasts.find(r=>r.contrast===`aim_minus_dino_${pattern}_fill${fill}`);
const family=r=>`${sign(r.estimate)} [${PP(r.familywise_ci_low)}, ${PP(r.familywise_ci_high)}]`;
function text(s,value,x,y,w,h,size=28,color=INK,bold=false){
 const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=value;sh.text.style={typeface:FONT,fontSize:size,color,bold,verticalAlignment:'top',insets:0,wrap:'square',autoFit:'none'};return sh;
}
function table(s,values,x,y,w,h,widths,size=23){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});
 t.borders.assign({style:'solid',fill:'#D8E1E4',width:.5});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?'#E9F4F3':'#FFFFFF';
  cell.text.style={typeface:FONT,fontSize:size,color:r===0?TEAL:INK,bold:r===0,verticalAlignment:'middle'};
 }return t;
}
function init(i){
 const s=p.slides.items[i],m=data.slides[i];s.hidden=false;
 text(s,m.title,64,43,1152,106,44,INK,true);
 text(s,String(i+1).padStart(2,'0'),1190,680,45,20,14,GRAY);
 s.speakerNotes.text=`TARGET: ${m.seconds} seconds\nANCHOR: ${m.anchor}\n\n${m.note}\n\nSOURCES: ${m.source}`;return s;
}
function chart(s,categories,series,x,y,w,h,yTitle='Accuracy (%)'){
 // Use the displayed one-decimal percentages in the editable workbook too.
 // This avoids pretending Excel preserves the full binary bootstrap precision.
 series=series.map(r=>({...r,values:r.values.map(n=>Number(n.toFixed(1)))}));
 const c=s.charts.add('bar',{position:{left:x,top:y,width:w,height:h},categories,series,
  barOptions:{direction:'column',grouping:'clustered',gapWidth:100},hasLegend:series.length>1,
  legend:{position:'bottom',overlay:false,textStyle:{fontSize:23,fill:INK}},
  chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0},
  xAxis:{textStyle:{fontSize:24,fill:INK},majorGridlines:null,line:{fill:'#B6C2C7',width:1}},
  yAxis:{min:0,max:100,majorUnit:20,numberFormatCode:'0',title:{text:yTitle,textStyle:{fontSize:22,fill:GRAY}},
   textStyle:{fontSize:20,fill:GRAY},line:{fill:'none',width:0},majorGridlines:{fill:'#E3E9EC',width:1}},
  dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0',textStyle:{fontSize:24,fill:INK,bold:true}}
 });applyPresentationChartFont(c,{fontFamily:FONT});return c;
}
const evidenceImage=new Uint8Array(await fs.readFile(path.join(ROOT,'results/extension_v2/figures/design_inputs.png')));
function specimen(s,col,row,x,y,size){
 // Crop the unchanged audited figure to its square input panel. Labels are native text.
 const im=s.images.add({blob:evidenceImage,contentType:'image/png',position:{left:x,top:y,width:size,height:size},fit:'cover',alt:`Audited ${row===0?'primary':'auxiliary'} input, figure column ${col+1}`});
 const left=[.006,.205,.405,.605,.804][col];
 im.crop={left,top:row===0?.127:.604,right:1-left-.191,bottom:row===0?.488:.011};return im;
}
function link(s,label,url,x,y,w,size=26){const t=text(s,label,x,y,w,45,size,TEAL,true);t.text.get(label).link={uri:url,isExternal:true};return t;}

// 1. Retain and update the existing cover objects in place.
{
 const s=p.slides.items[0],sh=s.shapes.items;
 sh.find(x=>String(x.text).startsWith('Separating')).text='Evaluation conditions, visible foreground and model ordering\nin frozen AIMv2 and DINOv2';
 sh.find(x=>String(x.text).startsWith('Boshen Yang')).text='Boshen Yang\nOxford-IIIT Pet, pilot and follow-up v2';
 const m=data.slides[0];s.speakerNotes.text=`TARGET: ${m.seconds} seconds\nANCHOR: ${m.anchor}\n\n${m.note}\n\nSOURCES: ${m.source}`;
}
// 2. Motivation
{
 const s=init(1);
 text(s,'Research question',64,179,1100,44,28,TEAL,true);
 text(s,'Does the masking condition change\nwhich model appears more robust?',64,240,1130,124,43,INK,true);
 text(s,'Measure retained foreground. Test the ordering on new images.\nUse same-image pairs to examine what area matching misses.',64,421,1130,114,29);
 text(s,'Contribution: a reproducible replication and diagnostic extension of prior occlusion work.',64,591,1125,70,23,GRAY);
}
// 3. Actual inputs and two denominators
{
 const s=init(2),id=data.example_selection.primary_image_id;
 const c=data.example_conditions.find(r=>r.image_id===id&&r.pattern==='center'&&r.fill==='128');
 const r=data.example_conditions.find(r=>r.image_id===id&&r.pattern==='random'&&r.fill==='128'&&r.repeat==='0');
 for(const [j,label] of ['Original','Center, 25% image visible','Random, 25% image visible'].entries()){
  text(s,label,64+j*398,177,370,40,25,INK,true);specimen(s,j,0,64+j*398,229,300);
 }
 text(s,`${id}\nIllustrative input`,64,547,360,66,23,GRAY);
 text(s,`${P(c.object_visibility)} foreground visible`,462,547,370,60,25,TEAL,true);
 text(s,`${P(r.object_visibility)} foreground visible`,860,547,370,60,25,TEAL,true);
 text(s,'Image visibility uses the whole image. Foreground visibility uses the annotated animal.',64,632,1140,36,23,GRAY);
}
// 4. Setup
{
 const s=init(3);
 table(s,[['Component','Fixed design'],['Data','Oxford-IIIT Pet, 37 breeds, pixel foreground labels'],['Original probe fit','1,480 clean train / 370 clean validation, C = 10'],['New main cohort','740 official-test images, 20 per breed, disjoint from pilot'],['Encoders and readout','Frozen AIMv2-L/14, DINOv2-L/14; mean patch pooling'],['Evaluation','Same 224x224 inputs, L2-normalized features, fixed probes'],['Follow-up timing','Design fixed after pilot and before new predictions']],64,174,1152,410,[270,882],23);
 text(s,'No refitting or parameter selection on follow-up images.',64,613,1120,49,30,TEAL,true);
}
// 5. Controls
{
 const s=init(4);
 table(s,[['Comparison','Held fixed','Still changes'],['Across models','Images, masks, preprocessing,\nprobe procedure','Pretraining data/objective,\nweights and model details'],['Gray versus black','Model, probe, mask,\nretained pixels','Hidden-pixel value'],['Same-image pairs','Image, model, probe,\noccluder area and shape','Occluder position, retained\nparts, texture and background']],64,176,1152,340,[235,460,457],24);
 text(s,'Cross-model scores describe these systems under shared inputs.',64,552,1140,48,29,TEAL,true);
 text(s,'They cannot identify the effect of prefix attention.',64,613,1140,44,29,INK,true);
}
// 6. Gray main result, native editable chart and paired intervals
{
 const s=init(5);
 text(s,'Gray fill, 25% visible image area, 740 new test images',64,157,1130,39,25,GRAY);
 chart(s,['Center','Random'],['aimv2','dinov2'].map((m,j)=>({name:j===0?'AIMv2':'DINOv2',values:['center','random'].map(q=>Number(stat(m,128,q).estimate)*100),fill:j===0?AIM:DINO})),64,208,1152,315);
 table(s,[['Paired AIMv2 minus DINOv2','Difference in pp [simultaneous 95% CI]'],['Center',family(contrast('center',128))],['Random',family(contrast('random',128))]],64,540,1152,114,[510,642],23);
}
// 7. Fill replication
{
 const s=init(6);
 const values=[['Fill','Pattern','AIMv2','DINOv2','AIM minus DINO, pp\n[simultaneous 95% CI]']];
 for(const fill of [128,0])for(const q of ['center','random'])values.push([fill===128?'Gray':'Black',q==='center'?'Center':'Random',P(stat('aimv2',fill,q).estimate),P(stat('dinov2',fill,q).estimate),family(contrast(q,fill))]);
 table(s,values,64,180,1152,300,[140,160,170,170,512],24);
 text(s,'Fill comparison keeps the visible pixels and mask locations identical.',64,515,1140,45,28,TEAL,true);
 // Differences are independently verified below and in the package review.
 text(s,'Random accuracy, black minus gray: AIMv2 -3.2 pp / DINOv2 -7.4 pp',64,576,1140,43,27);
 text(s,'Repeated ordering does not establish equivalent fills.',64,631,1140,36,23,GRAY);
}
// 8. Annotation measurements, native editable chart
{
 const s=init(7);
 text(s,'Mean foreground retained at 25% visible image area, n = 740',64,166,1140,40,26,GRAY);
 const order=['prefix','suffix','center','random'];
 chart(s,['Prefix','Suffix','Center','Random'],[{name:'Foreground visible',values:order.map(q=>Number(data.foreground.find(r=>r.pattern===q).mean)*100),fill:TEAL}],64,222,1152,333,'Foreground visible (%)');
 text(s,'Standard masks change content distribution as well as position.',64,580,1140,47,30,INK,true);
 text(s,'Foreground coverage does not quantify how much of the score gap it explains.',64,637,1140,33,23,GRAY);
}
// 9. Two diagnostic designs, not the main 25%-visible conditions
{
 const s=init(8);
 text(s,'These squares hide 25% of the image, leaving 75% visible.',64,165,1140,43,29,TEAL,true);
 text(s,'Foreground contrast: most versus least retained foreground.\nForeground-matched: gap <= 3 pp, separated occluder locations.',64,224,1140,91,27);
 const vals=[['Gray fill, n = 740','More foreground','Less foreground','Paired gap, pp [95% CI]']];
 for(const m of ['aimv2','dinov2']){const r=pair(m,128,'object_contrast');vals.push([m==='aimv2'?'AIMv2':'DINOv2',P(r.accuracy_a),P(r.accuracy_b),`${PP(r.paired_accuracy_difference)} [${PP(r.paired_accuracy_difference_ci_low)}, ${PP(r.paired_accuracy_difference_ci_high)}]`]);}
 table(s,vals,64,334,1152,171,[290,230,230,402],24);
 text(s,'Foreground-matched pairs: correct / wrong flips',64,542,1140,41,28,TEAL,true);
 text(s,`AIMv2 ${P(pair('aimv2',128,'visibility_matched').correctness_flip_rate)} / DINOv2 ${P(pair('dinov2',128,'visibility_matched').correctness_flip_rate)}. Lower flips alone do not mean higher robustness.`,64,599,1140,58,26);
}
// 10. Auxiliary head-region diagnostic
{
 const s=init(9);
 text(s,'Auxiliary trainval cohort: 159 / 185 images meet fixed pairing rules',64,157,1140,43,25,GRAY);
 for(const [j,label]of['Higher head visibility','Lower head visibility'].entries()){
  text(s,label,64+j*253,219,242,42,23,INK,true);specimen(s,j+1,1,64+j*253,272,224);
 }
 text(s,'Example pair, same square area\n75% image visible',64,517,495,72,24,GRAY);
 const vals=[['Gray fill','Higher head','Lower head','Gap (pp)']];
 for(const m of ['aimv2','dinov2']){const r=pair(m,128,'head_contrast');vals.push([m==='aimv2'?'AIMv2':'DINOv2',P(r.accuracy_a),P(r.accuracy_b),PP(r.paired_accuracy_difference)]);}
 table(s,vals,588,230,628,174,[145,164,164,155],23);
 const r=pair('aimv2',128,'head_contrast');
 text(s,`Mean foreground visible: ${P(r.mean_object_visibility_a)} / ${P(r.mean_object_visibility_b)}\nMean head region visible: ${P(r.mean_head_visibility_a)} / ${P(r.mean_head_visibility_b)}`,588,437,628,98,26,TEAL,true);
 text(s,'Parts and background change together. This does not isolate a head effect\nor explain the main crossover in another cohort.',64,610,1140,66,25);
}
// 11. Bounded conclusions
{
 const s=init(10);
 text(s,'Supported findings',64,178,535,46,29,TEAL,true);
 text(s,'Ordering changes with the condition\nand repeats on new images / two fills\n\nEqual image area retains unequal\nforeground\n\nSimilar foreground area still retains\ndifferent parts and background',64,246,553,314,28);
 text(s,'Remaining limits',688,178,528,46,29,TEAL,true);
 text(s,'Uncontrolled model pretraining\n\nContent and position still mixed\n\nOne dataset and one pooling recipe\n\nSynthetic constant-fill occlusion',688,246,528,314,28);
 text(s,'Contribution: measured evaluation behavior with explicit diagnostic limits.',64,607,1140,64,29,INK,true);
}
// 12. Concrete next experiment, repository and visible AI disclosure
{
 const s=init(11);
 text(s,'Next: feature-readout / pooling sensitivity',64,170,1140,49,32,TEAL,true);
 text(s,'Fix a new protocol. Fit on clean train, select on clean validation.\nLabel reuse of evaluated images as sensitivity analysis.\nLater: another dataset or natural occluders.',64,240,1140,147,28);
 link(s,'github.com/Bensssonxx/comp669-object-visibility','https://github.com/Bensssonxx/comp669-object-visibility',64,423,1152,29);
 text(s,'Private repository. Instructor access needs arranging before submission.',64,478,1140,41,23,GRAY);
 text(s,'AI use: OpenAI Codex assisted source review, code, debugging,\nexecution, analysis, slides and speaker-note drafting.',64,553,1140,88,26);
}
// 13. Hidden backup: all scores and statistical details
{
 const s=p.slides.add();s.hidden=true;s.background.fill='#FFFFFF';
 text(s,'Backup: full accuracy table and uncertainty',64,43,1152,100,42,INK,true);
 const vals=[['Model / fill','Clean','Prefix','Suffix','Center','Random']];
 for(const fill of[128,0])for(const m of['aimv2','dinov2'])vals.push([`${m==='aimv2'?'AIMv2':'DINOv2'} / ${fill===128?'gray':'black'}`,P(stat(m,-1,'clean').estimate),...['prefix','suffix','center','random'].map(q=>P(stat(m,fill,q).estimate))]);
 table(s,vals,64,177,1152,265,[295,171,171,171,172,172],23);
 text(s,'Clean = 100% image visible. All other columns = 25% image visible.\n10,000 breed-stratified image bootstrap resamples, repeated masks kept together.\nSeven planned contrasts receive Bonferroni simultaneous 95% intervals.\nIntervals condition on the fixed encoders and classifiers.',64,490,1140,164,25);
 s.speakerNotes.text='BACKUP ONLY. Skip during the 12-minute talk. The main sample has 20 images per breed, so image and breed-macro weighting agree. Average random repeats within image before resampling. Auxiliary estimates weight represented breeds equally after eligibility. The v1 lack of common foreground-support bins at 50% image visibility remains unresolved.\nSOURCES: results/extension_v2/summary.csv; primary_contrasts.csv; analysis_audit.json; docs/EXTENSION_V2_PROTOCOL.md';
}
// 14. Hidden backup: source links
{
 const s=p.slides.add();s.hidden=true;s.background.fill='#FFFFFF';text(s,'Backup: sources and reproducible evidence',64,43,1152,100,42,INK,true);
 const refs=[['Oxford-IIIT Pet, Parkhi et al. (2012)','https://www.robots.ox.ac.uk/~vgg/data/pets/'],['Intriguing Properties of Vision Transformers / PatchDrop (2021)','https://arxiv.org/abs/2105.10497'],['Noise or Signal: The Role of Image Backgrounds (2020)','https://arxiv.org/abs/2006.09994'],['AIMv2, official implementation','https://github.com/apple-aiml-research/ml-aim'],['DINOv2, official implementation','https://github.com/facebookresearch/dinov2'],['Project protocols, predictions and analysis','https://github.com/Bensssonxx/comp669-object-visibility']];
 for(const[j,[label,url]]of refs.entries())link(s,label,url,64,178+j*65,1152,26);
 text(s,'Dataset photos belong to their original owners. Source links also appear in speaker notes.',64,625,1140,40,22,GRAY);
 s.speakerNotes.text='BACKUP ONLY. Main protocols: docs/PROTOCOL.md and docs/EXTENSION_V2_PROTOCOL.md. Follow-up raw predictions and audit evidence: results/extension_v2/. AI disclosure: docs/AI_USE.md. The project is a replication and extension, not first-ever foreground/background analysis.\n'+refs.map(x=>x.join(': ')).join('\n');
}
await fs.writeFile(path.join(build,'final-inspection.ndjson'),(await p.inspect({kind:'slide,textbox,image,table,chart,notes',maxChars:1000000})).ndjson);
for(const [i,s]of p.slides.items.entries()){
 const png=await p.export({slide:s,format:'png',scale:1});await fs.writeFile(path.join(build,'previews',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const candidate=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
const finalPath=path.join(ROOT,`milestone/COMP669_Object_Visibility_Milestone_${process.env.MILESTONE_BUILD ?? 'v5'}.pptx`);
const nativeTables=[4,5,6,7,9,10,13],nativeCharts=[6,8];
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath,pythonExecutable:PYTHON,
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 explicitTotalSlideCount:14,requiredNativeTableOwnerSlides:nativeTables,requiredNativeChartOwnerSlides:nativeCharts,materializeLiteralChartWorkbooks:true,
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...nativeTables.flatMap(n=>['--require-native-table-slide',String(n)])],
 fontPolicy:{basis:'reference',families:[FONT],referencePath:source,referenceSha256:sourceHash},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
const words=txt=>(txt.match(/\b[\w]+(?:['’-][\w]+)*\b/g)??[]).length;
const totalWords=data.slides.reduce((n,s)=>n+words(s.note),0);
const timing={main_slides:12,hidden_backup_slides:[13,14],spoken_word_count:totalWords,planned_seconds:660,estimated_seconds_100wpm_plus40:totalWords/100*60+40,estimated_seconds_110wpm_plus40:totalWords/110*60+40,scope:'Word-rate estimate only, not a timed human rehearsal',slides:data.slides.map((s,i)=>({slide:i+1,words:words(s.note),target_seconds:s.seconds}))};
await fs.writeFile(path.join(ROOT,'milestone/TIMING_v5.json'),JSON.stringify(timing,null,2)+'\n');
let elapsed=0;
const en=['# Milestone v5 speaker notes','12 main slides, two hidden backups. Aim for 11 minutes, leaving one minute of margin. The script contains '+totalWords+' spoken words. At 100 words/minute plus 40 seconds of pauses it takes about '+Math.round(timing.estimated_seconds_100wpm_plus40/60*10)/10+' minutes. This is an estimate, not a timed rehearsal. Skip slides 13–14 unless a question requires them.','Read only the SCRIPT paragraphs aloud. Anchors, timing and source notes are rehearsal aids.'];
const stamp=n=>`${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`;
for(const[i,s]of data.slides.entries()){
 const end=elapsed+s.seconds;en.push(`## ${i+1}. ${s.title}\n\nTarget ${s.seconds}s. Cumulative ${stamp(elapsed)}–${stamp(end)}.\n\nAnchor: ${s.anchor}\n\nSCRIPT\n\n${s.note}\n\nSources: ${s.source}`);
 elapsed=end;
}
await fs.writeFile(path.join(ROOT,'milestone/SPEAKER_NOTES_EN_v5.md'),en.join('\n\n')+'\n');
console.log(JSON.stringify({finalPath,mainSlides:12,backups:2,timing,result},null,2));
