// Run a copy under .build-presentation/ to use the bundled artifact runtime.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {FileBlob,PresentationFile} from '@oai/artifact-tool';

const ROOT=process.cwd();
const SKILL=process.env.SKILL_DIR;
const PYTHON=process.env.RUNTIME_PYTHON;
if (!SKILL || !PYTHON) throw Error('Set SKILL_DIR and RUNTIME_PYTHON to the presentation runtime paths.');
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const data=JSON.parse(await fs.readFile(path.join(ROOT,'final/slide_data.json'),'utf8'));
for(const [file,hash] of Object.entries(data.source_hashes))if(crypto.createHash('sha256').update(await fs.readFile(path.join(ROOT,file))).digest('hex')!==hash)throw Error(`Changed source: ${file}`);
const source=path.join(ROOT,'milestone/COMP669_Object_Visibility_Milestone_v6.pptx');
const sourceHash=crypto.createHash('sha256').update(await fs.readFile(source)).digest('hex');
const p=await PresentationFile.importPptx(await FileBlob.load(source));
console.log('Imported the existing v6 deck.');
if(p.slides.items.length!==14||p.slides.items[0].frame.width!==1280)throw Error('Unexpected source deck');
const build=path.join(ROOT,'.build-presentation','completion');await fs.mkdir(path.join(build,'previews'),{recursive:true});
const before=await p.inspect({kind:'slide,textbox,shape,image,table,chart,layout',maxChars:1000000});
await fs.writeFile(path.join(build,'source-inspection.ndjson'),before.ndjson);
const records=before.ndjson.split('\n').filter(Boolean).map(x=>JSON.parse(x));
const ids=[...new Set(records.filter(r=>['textbox','shape','image','table','chart'].includes(r.kind)).map(r=>r.id))];
p.delete(ids);
const FONT='Arial',INK='#17313D',TEAL='#007F7B',GRAY='#52616A',COLORS=['#0072B2','#D55E00'];
const percent=n=>`${(Number(n)*100).toFixed(1)}%`,points=n=>(Number(n)*100).toFixed(1);
const stat=(cohort,fraction,pattern,model,fill=128)=>data.summary.find(r=>r.cohort===cohort&&r.fraction===fraction&&r.pattern===pattern&&r.metric===model&&r.fill===fill);
const pair=(cohort,model)=>data.pairs.find(r=>r.cohort===cohort&&r.pair_type==='head_contrast'&&r.model===model&&r.fill===128);
function text(s,value,x,y,w,h,size=28,color=INK,bold=false){
 const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=value;sh.text.style={typeface:FONT,fontSize:size,color,bold,verticalAlignment:'top',insets:0,wrap:'square',autoFit:'none'};return sh;
}
function table(s,values,x,y,w,h,widths,size=23){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});
 t.borders.assign({style:'solid',fill:'#D8E1E4',width:.5});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?'#E9F4F3':'#FFFFFF';cell.text.style={typeface:FONT,fontSize:size,color:r===0?TEAL:INK,bold:r===0,verticalAlignment:'middle'};
 }return t;
}
function init(i,title){const s=p.slides.items[i];s.hidden=i>=12;s.background.fill=i===0?'#F7FAFA':'#FFFFFF';
 text(s,title??data.slides[i].title,64,44,1152,110,44,INK,true);
 if(i>0)text(s,String(i+1).padStart(2,'0'),1190,680,45,20,14,GRAY);
 if(i<12)s.speakerNotes.text=data.slides[i].note+'\n\nSOURCES (not spoken): '+data.slides[i].source;
 return s;
}
async function photo(s,name,x,y,size){s.images.add({blob:new Uint8Array(await fs.readFile(path.join(ROOT,'final/assets',name+'.png'))),contentType:'image/png',position:{left:x,top:y,width:size,height:size},fit:'contain',alt:'Actual experiment input: '+name});}
function chart(s,type,series,x,y,w,h,{categories=[],xTitle='',yTitle='Accuracy (%)',yMin=0,yMax=100,xMin=0,xMax=100}={}){
 const c=s.charts.add(type,{position:{left:x,top:y,width:w,height:h},categories,series,hasLegend:true,
  legend:{position:'bottom',overlay:false,textStyle:{fontSize:20,fill:INK}},scatterOptions:{style:'lineWithMarkers'},lineOptions:{smooth:false},
  barOptions:{direction:'column',grouping:'clustered',gapWidth:100},displayBlanksAs:'gap',
  chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0},
  xAxis:{...(type==='scatter'?{min:xMin,max:xMax,majorUnit:25}:{}),numberFormatCode:'0',textStyle:{fontSize:19,fill:GRAY},
   ...(xTitle?{title:{text:xTitle,textStyle:{fontSize:20,fill:GRAY}}}:{}),majorGridlines:null,line:{fill:'#B6C2C7',width:1}},
  yAxis:{min:yMin,max:yMax,crossesAt:yMin,majorUnit:yMin<0?20:25,numberFormatCode:'0',title:{text:yTitle,textStyle:{fontSize:20,fill:GRAY}},
   textStyle:{fontSize:19,fill:GRAY},majorGridlines:{fill:'#E3E9EC',width:1},line:{fill:'none',width:0}},
  dataLabels:type==='bar'?{showValue:true,position:'outEnd',numberFormatCode:'0.0',textStyle:{fontSize:23,fill:INK,bold:true}}:{showValue:false}
 });applyPresentationChartFont(c,{fontFamily:FONT});
 if(yMin<0){c.xAxis.crossesAt=yMin;c.xAxis.tickLabelPosition='low';c.yAxis.crossesAt=xMin;}
 return c;
}
function series(name,values,index,xValues){return {name,values:values.map(v=>v===null?null:Number(v.toFixed(3))),...(xValues?{xValues:xValues.map(v=>Number(v.toFixed(3)))}:{}),fill:COLORS[index],line:{fill:COLORS[index],width:2},marker:{symbol:'circle',size:5,fill:COLORS[index]}};}

// 1. Keep the restrained cover style of the milestone deck.
{
 const s=p.slides.items[0];s.hidden=false;s.background.fill='#F7FAFA';
 text(s,'COMP 669 FINAL PROJECT',64,72,1000,35,20,TEAL,true);
 text(s,'Comparing AIMv2 and DINOv2\nUnder Occlusion',64,188,1152,180,52,INK,true);
 text(s,'Masking patterns, visible animal area,\nand retained animal regions',64,410,1100,110,32,GRAY);
 text(s,'Boshen Yang\nOxford-IIIT Pet',64,590,1000,65,23,GRAY);
 s.speakerNotes.text=data.slides[0].note+'\n\nSOURCES: '+data.slides[0].source;
}
{
 const s=init(1);text(s,'When does the masking pattern change\nwhich model performs better?',64,205,1140,130,43,INK,true);
 text(s,'Measure how much animal remains visible\nand which regions are retained.',64,395,1140,110,32,TEAL,true);
 text(s,'Purpose: make an occlusion score easier to interpret.',64,580,1140,60,27,GRAY);
}
{
 const s=init(2);text(s,'Oxford-IIIT Pet: 37 cat and dog breeds',64,163,1152,45,28,TEAL,true);
 table(s,[['Data','Images','Use'],['Clean training / validation','1,480 / 370','Fit and select classifiers'],['Main evaluation','740','Four patterns; 25%, 50%, 75% visible'],['New annotated evaluation','185','All patterns plus head-region pairs']],64,232,1152,257,[420,180,552],24);
 text(s,'Frozen encoders and classifiers. Shared masks, preprocessing and mean pooling.',64,535,1140,83,28,INK,true);
 text(s,'Training histories differ; these comparisons do not isolate a training mechanism.',64,635,1135,40,22,GRAY);
}
{
 const s=init(3);const labels=['Original','Center: 25% image visible','Random: 25% image visible'];
 for(let j=0;j<3;j++){text(s,labels[j],64+j*398,170,380,42,25,INK,true);await photo(s,'primary_'+['original','center','random'][j],64+j*398,225,300);}
 text(s,'Abyssinian_96',64,542,330,40,22,GRAY);
 for(let j=0;j<2;j++){const a=data.assets.find(a=>a.group==='primary'&&a.label===['center','random'][j]);text(s,`${percent(a.animal)} animal visible`,462+j*398,545,370,48,26,TEAL,true);}
 text(s,'Image visibility uses all pixels. Animal visibility uses labeled foreground pixels.',64,625,1152,50,25,GRAY);
}
{
 const s=init(4);text(s,'740 images; gray fill; 25% image visible',64,163,1140,45,27,GRAY);
 chart(s,'bar',['aimv2','dinov2'].map((m,i)=>series(m==='aimv2'?'AIMv2':'DINOv2',['center','random'].map(p=>100*stat('primary',.25,p,m).estimate),i)),95,235,1090,330,{categories:['Center','Random']});
 text(s,'Center favors AIMv2. Random favors DINOv2.',64,592,1152,49,31,TEAL,true);
 text(s,'The initial ordering also appears with black fill.',64,646,1152,36,23,GRAY);
}
{
 const s=init(5);text(s,'740 images; gray fill; 25% image visible',64,155,1140,40,26,GRAY);
 for(let i=0;i<2;i++){
  const pattern=['center','random'][i];text(s,pattern==='center'?'Center':'Random',64+i*610,205,540,38,27,INK,true);
  const q=data.bins.filter(r=>r.cohort==='primary'&&r.fraction===.25&&r.fill===128&&r.bin_width===.2&&r.convention==='image_average'&&r.pattern===pattern&&r.metric==='aimv2'&&r.estimable).sort((a,b)=>a.fg_bin-b.fg_bin);
  const ss=['aimv2','dinov2'].map((m,j)=>series(m==='aimv2'?'AIMv2':'DINOv2',q.map(r=>100*data.bins.find(t=>t.cohort==='primary'&&t.fraction===.25&&t.fill===128&&t.bin_width===.2&&t.convention==='image_average'&&t.pattern===pattern&&t.metric===m&&t.fg_bin===r.fg_bin).estimate),j,q.map(r=>100*r.foreground_mean)));
  chart(s,'scatter',ss,52+i*610,245,555,310,{xTitle:'Animal visible (%)'});
  text(s,'Images per shown point: '+q.map(r=>r.n_images).join(', '),64+i*610,565,555,43,22,GRAY);
 }
 text(s,'Different image groups; no extrapolation into empty intervals.',64,618,1150,40,27,TEAL,true);
 text(s,'Point estimates shown. Full four-pattern plots with 95% intervals are in the report.',64,663,1150,29,19,GRAY);
}
{
 const s=init(6);
 text(s,'25% of each image visible, gray fill. Animal coverage differs by at most 3 pp per pair.',64,155,1152,55,26,GRAY);
 const assets=data.assets.filter(a=>a.group==='relocation');
 for(const [i,a] of assets.entries()){
   const x=64+244*i; await photo(s,'relocation_'+a.label,x,238,216);
   text(s,a.label==='center'?'Center':'Relocated',x,474,220,40,25,INK,true);
   text(s,`Animal: ${percent(a.animal)}`,x,522,230,35,20,GRAY);
 }
 const rows=[['Model','Center','Relocated']];
 const pairs=data.relocation.filter(r=>r.cohort==='primary' && r.metric!=='interaction');
 for(const r of pairs)rows.push([r.metric==='aimv2'?'AIMv2':'DINOv2',percent(r.center_acc),percent(r.relocated_acc)]);
 text(s,`Breed accuracy on ${pairs[0].eligible} matched photos`,574,224,640,65,27,TEAL,true);
 table(s,rows,574,300,640,168,[215,200,225],24);
 text(s,'Two relocated masks per photo. Each moves at least 16 of the 64 visible patches.',574,493,640,84,23,GRAY);
 text(s,`Mean animal visibility: ${percent(pairs[0].center_animal)} center and ${percent(pairs[0].relocated_animal)} relocated.`,64,612,1152,72,27,INK,true);
}
{
 const s=init(7);text(s,'Same 740 images and fixed systems; all four patterns tested',64,158,1152,42,26,GRAY);
 for(let i=0;i<2;i++){
  const fill=[128,0][i];text(s,fill===128?'Gray fill':'Black fill',64+i*610,215,550,40,27,INK,true);
  chart(s,'scatter',['center','random'].map((pat,j)=>series(pat==='center'?'Center':'Random',[.25,.5,.75].map(f=>100*stat('primary',f,pat,'aim_minus_dino',fill).estimate),j,[25,50,75])),52+i*610,260,555,310,{xTitle:'Image visible (%)',yTitle:'AIM minus DINO (pp)',yMin:-40,yMax:40,xMin:25,xMax:75});
 }
 text(s,'Positive gap: AIMv2 leads. Negative gap: DINOv2 leads.',64,605,1152,45,29,TEAL,true);
 text(s,`75% visible, gray random masks: loss from clean accuracy is ${points(data.clean_loss.aimv2_loss)} pp for AIMv2 and ${points(data.clean_loss.dinov2_loss)} pp for DINOv2.`,64,654,1152,38,21,GRAY);
}
{
 const s=init(8);const r=pair('auxiliary_head','aimv2');text(s,'159 eligible pairs; same-size square; 75% image visible',64,158,1152,40,26,GRAY);
 await photo(s,'head_high',64,235,260);await photo(s,'head_low',350,235,260);
 text(s,'Higher head coverage',64,505,280,38,24,INK,true);text(s,'Lower head coverage',350,505,280,38,24,INK,true);
 for(let i=0;i<2;i++){const a=data.assets.find(a=>a.group==='head'&&a.label===['high','low'][i]);text(s,`Animal ${percent(a.animal)}; head ${percent(a.head)}`,64+i*286,546,285,32,19,GRAY);}
 text(s,'Cohort means',665,202,550,34,24,TEAL,true);
 table(s,[['Mean visible','Higher head','Lower head'],['Animal',percent(r.object_visibility_a),percent(r.object_visibility_b)],['Head ROI',percent(r.head_visibility_a),percent(r.head_visibility_b)],['Other animal',percent(r.body_visibility_a),percent(r.body_visibility_b)],['Background',percent(r.background_visibility_a),percent(r.background_visibility_b)]],665,240,550,280,[220,165,165],23);
 text(s,'Head coverage changes together with other visible content.',64,591,1152,50,30,TEAL,true);
 text(s,'Head ROI = annotated head box intersected with foreground; not precise head segmentation.',64,652,1152,40,22,GRAY);
}
{
 const s=init(9);text(s,'185 unused annotated images; gray fill; fixed sampling before predictions',64,157,1152,60,26,GRAY);
 const rows=[['Image visible','Pattern','AIMv2','DINOv2']];
 for(const f of [.25,.5,.75])for(const pat of ['center','random'])rows.push([`${Math.round(f*100)}%`,pat,percent(stat('new_head',f,pat,'aimv2').estimate),percent(stat('new_head',f,pat,'dinov2').estimate)]);
 table(s,rows,64,238,1152,343,[280,300,286,286],26);
 text(s,'Random at 50% / 75%: adjusted intervals do not resolve a winner.\nSeparate cohort: unused official trainval images with head annotations.',64,605,1152,70,23,GRAY);
}
{
 const s=init(10),r=pair('new_head','aimv2');text(s,`${r.n_images} of 185 images meet the unchanged head-pair rules`,64,158,1152,45,28,TEAL,true);
 text(s,'Breed accuracy; gray fill; 75% image visible',64,210,1152,32,23,GRAY);
 const rows=[['Model','More head visible','Less head visible','Gap (pp)']];
 for(const m of ['aimv2','dinov2']){const q=pair('new_head',m);rows.push([m==='aimv2'?'AIMv2':'DINOv2',percent(q.accuracy_a),percent(q.accuracy_b),points(q.difference)]);}
 table(s,rows,64,249,1152,185,[220,340,340,252],26);
 text(s,`Animal visible: ${percent(r.object_visibility_a)} / ${percent(r.object_visibility_b)}\nHead ROI visible: ${percent(r.head_visibility_a)} / ${percent(r.head_visibility_b)}\nOther animal visible: ${percent(r.body_visibility_a)} / ${percent(r.body_visibility_b)}\nBackground visible: ${percent(r.background_visibility_a)} / ${percent(r.background_visibility_b)}`,64,475,1152,140,27,INK,true);
 text(s,'A new-image check of a content bundle, not an isolated head effect.',64,645,1152,40,25,GRAY);
}
{
 const s=init(11);text(s,'Model ranking changes with pattern and visibility.',64,184,1152,60,33,TEAL,true);
 text(s,'Masked accuracy and loss from clean accuracy can favor different models.',64,273,1152,92,32,TEAL,true);
 text(s,'At matched animal area, moving visible patches affected the models in opposite directions.',64,370,1152,96,32,TEAL,true);
 text(s,'Scope: two fixed systems, one dataset, artificial masks.\nTraining mechanisms and real-world occluders remain untested.',64,485,1152,90,27,GRAY);
 const link=text(s,'github.com/Bensssonxx/comp669-object-visibility',64,594,1152,40,25,TEAL,true);link.text.get('github.com/Bensssonxx/comp669-object-visibility').link={uri:'https://github.com/Bensssonxx/comp669-object-visibility',isExternal:true};
 text(s,'I used OpenAI Codex for source review, code, experiments, analysis, slides and notes.',64,648,1152,55,18,GRAY);
}
{
 const s=init(12,'Backup: all patterns at each visibility budget');
 const rows=[['Image visible','Pattern','AIMv2 / gray','DINOv2 / gray','AIMv2 / black','DINOv2 / black']];
 for(const f of [.25,.5,.75])for(const pat of ['prefix','suffix','center','random'])rows.push([`${Math.round(f*100)}%`,pat,...[128,0].flatMap(fill=>['aimv2','dinov2'].map(m=>percent(stat('primary',f,pat,m,fill).estimate)))]);
 const t=table(s,rows,64,175,1152,450,[180,170,200,200,201,201],20);
 t.cells.block({row:0,column:0,rowCount:rows.length,columnCount:6}).assign({margins:{top:2,bottom:2,left:9.6,right:9.6}});
 text(s,'740 images; random repeats averaged per original image. Full paired intervals are in accuracy_summary.csv.',64,648,1152,45,21,GRAY);
 s.speakerNotes.text='Backup only. Source: results/occlusion_completion/accuracy_summary.csv. Pointwise and 12-contrast simultaneous model-gap intervals are in the CSV.';
}
{
 const s=init(13,'Backup: sources and interpretation limits');
 const entries=[['Oxford-IIIT Pet','https://www.robots.ox.ac.uk/~vgg/data/pets/'],['AIMv2 official implementation','https://github.com/apple/ml-aim'],['DINOv2 official implementation','https://github.com/facebookresearch/dinov2'],['PatchDrop / Intriguing Properties of Vision Transformers','https://arxiv.org/html/2105.10497v3'],['Image Recognition Under Occlusion','https://arxiv.org/html/2409.10775v1']];
 entries.forEach(([label,url],i)=>{const t=text(s,label,64,180+i*65,1152,50,26,TEAL,true);t.text.get(label).link={uri:url,isExternal:true};});
 text(s,'Pixel masking measures behavior. It does not identify a pretraining cause.\nHead boxes are region proxies; source split and image composition remain limitations.',64,548,1152,100,25,GRAY);
 text(s,`Main clean accuracy: AIMv2 ${percent(stat('primary',1,'clean','aimv2',-1).estimate)}; DINOv2 ${percent(stat('primary',1,'clean','dinov2',-1).estimate)}.`,64,655,1152,32,21,GRAY);
 s.speakerNotes.text='Sources: '+entries.map(x=>x[1]).join('; ')+'. Dataset photos belong to their original owners. Code, data lineage and AI assistance are disclosed in the repository.';
}
for(let i=0;i<p.slides.items.length;i++){
 const s=p.slides.items[i];const blob=await s.export({format:'png',scale:1});await fs.writeFile(path.join(build,'previews',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
 console.log('Rendered slide',i+1);
}
await fs.writeFile(path.join(build,'inspection.ndjson'),(await p.inspect({kind:'slide,textbox,image,table,chart,notes,layout',maxChars:1000000})).ndjson);
const candidate=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
const finalPath=path.join(ROOT,'final',process.env.FINAL_DECK_NAME??'COMP669_Occlusion_Final_v3.pptx');
const receipt=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath,pythonExecutable:PYTHON,
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[3,7,9,10,11,13].flatMap(n=>['--require-native-table-slide',String(n)])],
 explicitTotalSlideCount:14,requiredNativeTableOwnerSlides:[3,7,9,10,11,13],requiredNativeChartOwnerSlides:[5,6,8],
 fontPolicy:{basis:'reference',families:[FONT],referencePath:source,referenceSha256:sourceHash},
 materializeLiteralChartWorkbooks:true,verifyArtifactToolImport:true,receiptPath:path.join(build,path.basename(finalPath).replace('.pptx','.validation.json'))});
console.log(JSON.stringify({finalPath,receipt}));
