import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {PresentationFile, FileBlob} from '@oai/artifact-tool';

// Run a copy in .build-presentation/, whose node_modules links to the bundled runtime.
const ROOT=process.cwd();
const SKILL='/Users/boshenyang/.codex/plugins/cache/openai-primary-runtime/presentations/26.1017.22136/skills/presentations';
const PYTHON='/Users/boshenyang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
process.env.RUNTIME_NODE_MODULES ??= '/Users/boshenyang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
process.env.RUNTIME_NODE ??= process.execPath;
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const data=JSON.parse(await fs.readFile(path.join(ROOT,'milestone/slide_data_v6.json'),'utf8'));
if(!data.audit.passed||!data.analysis_audit.passed) throw Error('Completed audited v2 evidence required.');
for(const [file,hash] of Object.entries(data.evidence_sha256)){
 if(crypto.createHash('sha256').update(await fs.readFile(path.join(ROOT,file))).digest('hex')!==hash) throw Error(`Evidence changed: ${file}`);
}
const source=path.join(ROOT,'milestone/COMP669_Object_Visibility_Milestone_v4.pptx');
const sourceHash=crypto.createHash('sha256').update(await fs.readFile(source)).digest('hex');
const p=await PresentationFile.importPptx(await FileBlob.load(source));
if(p.slides.items.length!==12||p.slides.items[0].frame.width!==1280||p.slides.items[0].frame.height!==720) throw Error('Unexpected source deck');
const build=path.join(ROOT,'.build-presentation',process.env.MILESTONE_BUILD ?? 'v6');
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
 sh.find(x=>String(x.text).startsWith('What does occlusion')).text='Comparing AIMv2 and DINOv2\nUnder Occlusion';
 sh.find(x=>String(x.text).startsWith('Separating')).text='Masking patterns and visible animal regions\non Oxford-IIIT Pet';
 sh.find(x=>String(x.text).startsWith('Boshen Yang')).text='Boshen Yang\nOxford-IIIT Pet, pilot and follow-up v2';
 const m=data.slides[0];s.speakerNotes.text=`TARGET: ${m.seconds} seconds\nANCHOR: ${m.anchor}\n\n${m.note}\n\nSOURCES: ${m.source}`;
}
// 2. One research question
{
 const s=init(1);
 text(s,'Does changing the masking pattern change\nwhich model performs better?',64,224,1152,135,43,INK,true);
 text(s,'The test we choose may affect which model we pick.',64,458,1140,82,31,GRAY);
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
// 4. Explain how the two test samples relate
{
 const s=init(3);
 text(s,'One dataset: Oxford-IIIT Pet, 37 breeds',64,165,1152,45,30,TEAL,true);
 table(s,[['Stage','Images','Purpose'],['Train / validation','1,480 / 370','Fit classifiers / choose settings'],['First test','185 (5 per breed)','Explore the pattern'],['Second test','740 different images\n(20 per breed)','Check whether it repeats']],64,240,1152,280,[265,330,557],25);
 text(s,'Same dataset. Same frozen models and classifiers.\nNo retraining on either test set.',64,567,1140,94,30,INK,true);
}
// 5. Controls in plain language
{
 const s=init(4);
 table(s,[['Comparison','What stays the same?','What changes?'],['Two models','Pictures, masks,\nclassifier fitting method','Model and its training history'],['Gray / black','Model, picture, mask,\nvisible pixels','Fill color only'],['Moving a square','Picture, model,\nsquare size and shape','Visible parts and background']],64,180,1152,340,[240,460,452],25);
 text(s,'Different training histories remain uncontrolled.\nThese tests cannot isolate which training choice caused a difference.',64,566,1140,90,29,INK,true);
}
// 6. Main result
{
 const s=init(5);
 text(s,'Second test: 740 images, gray fill, 25% of each image visible',64,157,1152,45,25,GRAY);
 chart(s,['Center','Random'],['aimv2','dinov2'].map((m,j)=>({name:j===0?'AIMv2':'DINOv2',values:['center','random'].map(q=>Number(stat(m,128,q).estimate)*100),fill:j===0?AIM:DINO})),64,220,1152,335);
 text(s,'All four patterns tested. Main comparison: Center and Random.',64,203,1152,30,22,GRAY);
 text(s,'Center: AIMv2 does better. Random: DINOv2 does better.',64,595,1152,65,30,TEAL,true);
}
// 7. Repeat the comparison with black fill
{
 const s=init(6);
 const values=[['Fill','Pattern','AIMv2 accuracy','DINOv2 accuracy']];
 for(const fill of [128,0])for(const q of ['center','random'])values.push([fill===128?'Gray':'Black',q==='center'?'Center':'Random',P(stat('aimv2',fill,q).estimate),P(stat('dinov2',fill,q).estimate)]);
 table(s,values,64,187,1152,300,[220,270,331,331],27);
 text(s,'Same visible pixels and mask positions. Only the fill color changes.',64,533,1152,80,29,TEAL,true);
 text(s,'The ordering repeats under gray and black. The scores still change.',64,622,1152,48,25,GRAY);
}
// 8. Measure animal visibility
{
 const s=init(7);
 text(s,'All patterns keep 25% of the picture. Animal visibility differs.',64,166,1152,45,27,GRAY);
 const order=['prefix','suffix','center','random'];
 chart(s,['Top (prefix)','Bottom (suffix)','Center','Random'],[{name:'Animal visible',values:order.map(q=>Number(data.foreground.find(r=>r.pattern===q).mean)*100),fill:TEAL}],64,232,1152,330,'Animal visible (%)');
 text(s,'Mask location and visible content change together.',64,585,1152,48,31,INK,true);
 text(s,'This does not tell us how much animal visibility explains the score gap.',64,643,1152,32,23,GRAY);
}
// 9. Two same-image checks
{
 const s=init(8);
 text(s,'A square covers 25%. The other 75% stays visible.',64,165,1152,48,31,TEAL,true);
 text(s,'Move the same-sized square to leave more or less animal visible.',64,237,1152,75,28);
 const vals=[['Gray fill, 740 images','More animal visible','Less animal visible']];
 for(const m of ['aimv2','dinov2']){const r=pair(m,128,'object_contrast');vals.push([m==='aimv2'?'AIMv2':'DINOv2',P(r.accuracy_a),P(r.accuracy_b)]);}
 table(s,vals,64,329,1152,171,[350,401,401],26);
 text(s,'Match animal visibility within 3 percentage points:',64,538,1152,45,28,TEAL,true);
 text(s,`Correct / wrong switches: AIMv2 ${P(pair('aimv2',128,'visibility_matched').correctness_flip_rate)}, DINOv2 ${P(pair('dinov2',128,'visibility_matched').correctness_flip_rate)}.\nFewer switches alone do not mean better performance.`,64,596,1152,75,26);
}
// 10. Auxiliary head-region diagnostic
{
 const s=init(9);
 text(s,'Separate check: 159 of 185 images meet the pairing rules',64,157,1140,43,25,GRAY);
 for(const [j,label]of['Higher head visibility','Lower head visibility'].entries()){
  text(s,label,64+j*253,219,242,42,23,INK,true);specimen(s,j+1,1,64+j*253,272,224);
 }
 text(s,'Example pair, same square area\n75% image visible',64,517,495,72,24,GRAY);
 const vals=[['Gray fill','Higher head','Lower head','Gap (pp)']];
 for(const m of ['aimv2','dinov2']){const r=pair(m,128,'head_contrast');vals.push([m==='aimv2'?'AIMv2':'DINOv2',P(r.accuracy_a),P(r.accuracy_b),PP(r.paired_accuracy_difference)]);}
 table(s,vals,588,230,628,174,[145,164,164,155],23);
 const r=pair('aimv2',128,'head_contrast');
 text(s,`Mean foreground visible: ${P(r.mean_object_visibility_a)} / ${P(r.mean_object_visibility_b)}\nMean head region visible: ${P(r.mean_head_visibility_a)} / ${P(r.mean_head_visibility_b)}`,588,437,628,98,26,TEAL,true);
 text(s,'Other parts and background change too.\nThis does not isolate the effect of the head.',64,610,1140,66,25);
}
// 11. Findings and limits
{
 const s=init(10);
 text(s,'Findings',64,178,535,46,30,TEAL,true);
 text(s,'The better model changes with the mask.\nThis repeats with gray and black fill.\n\nEqual picture area can leave different\namounts of animal visible.\n\nSimilar animal area can still show\ndifferent parts.',64,246,570,314,28);
 text(s,'Limits',688,178,528,46,30,TEAL,true);
 text(s,'Training differs between models.\n\nMask position and content\nchange together.\n\nOne dataset and artificial masks.',688,246,528,314,28);
 text(s,'The result describes these models under these test conditions.',64,620,1152,50,29,INK,true);
}
// 12. Planned visibility and pooling checks, code and AI use
{
 const s=init(11);
 text(s,'1. Does the reversal persist with less occlusion?',64,166,1152,46,31,TEAL,true);
 text(s,'Test 50% and 75% image visibility across all four patterns.\nReuse the same 740 images, frozen models and classifiers.',64,224,1152,80,26);
 text(s,'2. Does feature averaging affect the reversal?',64,326,1152,46,31,TEAL,true);
 text(s,'Compare mean pooling with max pooling for both models.\nFit classifiers on clean training data. Select settings on validation.',64,384,1152,80,26);
 text(s,'Planned checks. Both reuse previously evaluated images.',64,479,1152,36,23,GRAY);
 link(s,'github.com/Bensssonxx/comp669-object-visibility','https://github.com/Bensssonxx/comp669-object-visibility',64,531,1152,26);
 text(s,'Public repository with protocols, code, predictions and analysis.',64,572,1152,32,22,GRAY);
 text(s,'AI use: Codex helped with source review, code, experiments,\nanalysis and presentation drafting.',64,619,1152,56,22);
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
p.slides.items[12].speakerNotes.text += '\nTECHNICAL NOTES: '+Object.values(data.technical_notes).join('\n')+'\nMODEL DIFFERENCES: '+data.contrasts.filter(r=>r.contrast.startsWith('aim_minus_dino_')).map(r=>r.contrast+': '+family(r)).join('\n');
await fs.writeFile(path.join(build,'final-inspection.ndjson'),(await p.inspect({kind:'slide,textbox,image,table,chart,notes',maxChars:1000000})).ndjson);
for(const [i,s]of p.slides.items.entries()){
 const png=await p.export({slide:s,format:'png',scale:1});await fs.writeFile(path.join(build,'previews',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const candidate=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
const finalPath=path.join(ROOT,`milestone/COMP669_Object_Visibility_Milestone_${process.env.MILESTONE_BUILD ?? 'v6'}.pptx`);
const nativeTables=[4,5,7,9,10,13],nativeCharts=[6,8];
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath,pythonExecutable:PYTHON,
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 explicitTotalSlideCount:14,requiredNativeTableOwnerSlides:nativeTables,requiredNativeChartOwnerSlides:nativeCharts,materializeLiteralChartWorkbooks:true,
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...nativeTables.flatMap(n=>['--require-native-table-slide',String(n)])],
 fontPolicy:{basis:'reference',families:[FONT],referencePath:source,referenceSha256:sourceHash},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
const words=txt=>(txt.match(/\b[\w]+(?:['’-][\w]+)*\b/g)??[]).length;
const totalWords=data.slides.reduce((n,s)=>n+words(s.note),0);
const timing={main_slides:12,hidden_backup_slides:[13,14],spoken_word_count:totalWords,estimated_seconds_90wpm_plus40:totalWords/90*60+40,planned_seconds:data.slides.reduce((n,s)=>n+s.seconds,0),estimated_seconds_100wpm_plus40:totalWords/100*60+40,estimated_seconds_110wpm_plus40:totalWords/110*60+40,scope:'Word-rate estimate only, not a timed human rehearsal',slides:data.slides.map((s,i)=>({slide:i+1,words:words(s.note),target_seconds:s.seconds}))};
await fs.writeFile(path.join(ROOT,'milestone/TIMING_v6.json'),JSON.stringify(timing,null,2)+'\n');
let elapsed=0;
const en=['# Complete milestone speech','This is the complete spoken script for slides 1–12, including the opening, slide transitions and closing. Read the paragraphs below each timing line. Do not read headings, timing lines or the source appendix aloud. Slides 13–14 are hidden backups for questions.','The script contains '+totalWords+' spoken words. At 90-100 words/minute plus 40 seconds for pauses and slide changes, the estimate is '+(timing.estimated_seconds_100wpm_plus40/60).toFixed(1)+'-'+(timing.estimated_seconds_90wpm_plus40/60).toFixed(1)+' minutes. This is a word-rate estimate, not a timed rehearsal.'];
const stamp=n=>`${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`;
for(const[i,s]of data.slides.entries()){
 const end=elapsed+s.seconds;en.push(`## Slide ${i+1}. ${s.title}\n\nTiming guide: ${stamp(elapsed)}–${stamp(end)}. About ${s.seconds} seconds.\n\n${s.note}`);
 elapsed=end;
}
en.push('## Source appendix (not spoken)',...data.slides.map((s,i)=>`Slide ${i+1}: ${s.source}`));
await fs.writeFile(path.join(ROOT,'milestone/SPEAKER_NOTES_EN_v6.md'),en.join('\n\n')+'\n');
console.log(JSON.stringify({finalPath,mainSlides:12,backups:2,timing,result},null,2));
