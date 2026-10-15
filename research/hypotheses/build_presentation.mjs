import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';

const workspace=process.env.HYPOTHESIS_WORKSPACE;
if(!workspace) throw new Error('Set HYPOTHESIS_WORKSPACE to the task workspace');
const skill='/root/.codex/skills/builtins/presentations';
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const root=path.join(workspace,'f1-pit-predictor-dataset/research/hypotheses');
const s=JSON.parse(await fs.readFile(path.join(root,'evaluation/summary.json'),'utf8'));
const prior=JSON.parse(await fs.readFile(path.join(workspace,'f1-pit-predictor-dataset/research/race-context/evaluation/summary.json'),'utf8'));
const build=path.join(workspace,'presentation-build');const out=path.join(workspace,'output');
await fs.mkdir(build,{recursive:true});await fs.mkdir(out,{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:720}});
const FONT='Nimbus Sans',INK='#13283F',BLUE='#005E9B',GRAY='#536477';
const ids=['RF_CONTEXT','H1_PERCENT','H2_DETAIL','H3_BOOST','H4_RECENT'];
const names={RF_CONTEXT:'Current forest',H1_PERCENT:'H1 Percentages',H2_DETAIL:'H2 Detailed forest',H3_BOOST:'H3 Boosting',H4_RECENT:'H4 Recent seasons'};
const models={...s.models,RF_CONTEXT:s.reference};
const pct=x=>x==null?'Undefined':(100*x).toFixed(1)+'%';
const num=x=>x.toLocaleString('en-US');
const score=n=>s.means[n].toFixed(4);
function text(sl,t,x,y,w,h,size=26,color=INK,bold=false){
 const sh=sl.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{style:'solid',fill:'none',width:0}});
 sh.text=t;sh.text.style={typeface:FONT,fontSize:size,color,bold};return sh;
}
function slide(title,notes=''){
 const sl=p.slides.add();sl.background.fill='#FFFFFF';text(sl,title,64,42,1152,95,44,INK,true);
 text(sl,`${p.slides.items.length} / 10`,1120,678,95,24,16,GRAY);
 sl.speakerNotes.text=notes+'\nSources: https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/pull/60 . research/hypotheses/REGISTRATION.md, REPORT.md and private immutable evaluation/summary.json. Development data only. No new 2026 evidence.';
 return sl;
}
function table(sl,values,widths,y=160,height=380,size=24){
 const t=sl.tables.add({rows:values.length,columns:values[0].length,left:64,top:y,width:1152,height,columnWidths:widths,values});
 t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({fill:'#FFFFFF',textStyle:{typeface:FONT,fontSize:size,color:INK},margins:{left:10,right:10,top:10,bottom:8},anchor:'center'});
 t.cells.block({row:0,column:0,rowCount:1,columnCount:values[0].length}).assign({fill:INK,textStyle:{typeface:FONT,fontSize:size,bold:true,color:'#FFFFFF'}});
 t.borders.assign({style:'solid',fill:'#D5DEE6',width:.6});
 return t;
}
const chosen=s.recommended,best=s.raw_best;const alert=models[chosen].practical.diagnostic_2025,conf=alert.checkpoint;

{
 const sl=slide('Pit-stop prediction experiments');
 text(sl,'Four hypotheses, trained and tested',64,164,1100,90,46,BLUE,true);
 text(sl,`${names[chosen]} is the registered recommendation`,64,282,1110,90,36,INK,true);
 text(sl,`Probability score: ${score(chosen)}\n2025 alert precision: ${pct(conf.precision)}. Recall: ${pct(conf.recall)}.`,64,402,1100,120,30);
 text(sl,'Exploratory pre-2026 development results. Lower probability score is better.',64,582,1100,56,23,GRAY);
}
{
 const sl=slide('The four hypotheses','All procedures are fixed before scoring. Each changes the reference, not the preceding hypothesis. H1 retains inverse scheduled distance. H2 changes depth and leaf size jointly. H4 includes matching terminal-allocation refit.');
 table(sl,[['Test','Hypothesis','Change'],['H1','Race percentages transfer better','Scale grid and tyre age by scheduled laps'],['H2','Useful patterns need more detail','Deeper trees and smaller leaves'],['H3','Boosting learns stronger patterns','Replace forest with 150 boosting iterations'],['H4','Recent seasons matter more','Train on the latest two admitted seasons']],[100,480,572],164,400,25);
 text(sl,'Same causal race inputs: tyres, completed-lap pace, position and numeric gaps.',64,602,1152,55,24,GRAY);
}
{
 const sl=slide('Training and evaluation','H1-H3 use all earlier admitted races. H4 uses the latest two earlier admitted seasons. 2018 is training only. No admitted 2022 season exists. Unknown outcomes are retained but not assigned no-stop labels. Thresholds use validation through 2024 and apply unchanged in 2025. All of this is development, not fresh confirmation.');
 table(sl,[['Validation year','Earlier races, H1–H3','Validation races'],...[[2019,18,19],[2020,37,12],[2021,49,16],[2023,65,21],[2024,86,23],[2025,109,24]].map(r=>r.map(String))],[300,480,372],154,364,24);
 text(sl,'93,650 identical scored checkpoints across 115 races',64,548,1152,48,30,BLUE,true);
 text(sl,'29,166 eligible outcomes remain unknown. No new 2026 data were opened.',64,610,1152,46,24,GRAY);
}
{
 const sl=slide('Probability scores for every hypothesis','Mean full-distribution negative log probability of the observed region/no-event outcome. Lower is better. Positive improvement favours the hypothesis. These values are not percentage accuracy. Intervals cluster by race and condition on the fitted procedures.');
 table(sl,[['Model','Log score','Improvement','95% interval'],...ids.map(n=>[names[n],score(n),n==='RF_CONTEXT'?'Reference':s.models[n].improvement_over_reference.mean.toFixed(4),n==='RF_CONTEXT'?'':s.models[n].improvement_over_reference.cr2_95.map(v=>v.toFixed(4)).join(' to ')])],[335,175,190,452],165,357,24);
 text(sl,'Lower score means less penalty for the observed stop timing or no-stop result.',64,556,1152,65,25);
 text(sl,'A score change does not directly measure the percentage of correct alerts.',64,620,1152,36,23,GRAY);
}
{
 const sl=slide('Scores across validation seasons','Seasonal log scores on the same matched scored checkpoints. The chart axis is restricted to the displayed score range to show differences. Scores across seasons also reflect different race composition and censoring.');
 const colors=['#13283F','#16857B','#D17B20','#7A4BA5','#3F7FBA'];
 const allScores=ids.flatMap(n=>['2019','2020','2021','2023','2024','2025'].map(y=>n==='RF_CONTEXT'?prior.by_season[y].models.RF_CONTEXT.mean_log_score:s.models[n].by_season[y].mean_log_score));
 const chart=sl.charts.add('line',{position:{left:64,top:155,width:1152,height:440},categories:['2019','2020','2021','2023','2024','2025'],series:ids.map((n,i)=>({name:names[n],values:['2019','2020','2021','2023','2024','2025'].map(y=>n==='RF_CONTEXT'?prior.by_season[y].models.RF_CONTEXT.mean_log_score:s.models[n].by_season[y].mean_log_score),line:{style:'solid',fill:colors[i],width:2.5}})),hasLegend:true,legend:{position:'bottom',textStyle:{typeface:FONT,fontSize:19}},xAxis:{textStyle:{typeface:FONT,fontSize:22}},yAxis:{min:Math.floor(Math.min(...allScores)*10)/10,max:Math.ceil(Math.max(...allScores)*10)/10,textStyle:{typeface:FONT,fontSize:20},numberFormatCode:'0.00',majorGridlines:{style:'solid',fill:'#D5DEE6',width:.6}},lineOptions:{smooth:false}});
 applyPresentationChartFont(chart,{fontFamily:FONT});
 text(sl,'Lower is better. The race mix and unknown-outcome share differ by season.',64,618,1152,44,24,GRAY);
}
{
 const sl=slide('What the experiments establish','Interpretations refer to matched development comparisons. Confidence intervals do not include training/selection variability. No causal claim about a single hyperparameter is made.');
 const interpretations=JSON.parse(await fs.readFile(path.join(root,'INTERPRETATIONS.json'),'utf8'));
 for(let i=0;i<4;i++){
  text(sl,names[ids[i+1]],64,160+i*117,295,90,28,BLUE,true);
  text(sl,interpretations[ids[i+1]],380,160+i*117,825,102,25);
 }
}
{
 const sl=slide('Exploratory 2025 alert performance','Threshold maximizes F1 through 2024 on 0.01..0.99, ties highest. 2025 remains previously exposed development. Alerts concern first up to three canonical regions, usually current lap plus next two, with an open-ended last region in short grids. Multiple alerts may concern one stop.');
 table(sl,[['Model','Precision','Recall','False alerts','Stops found'],...ids.map(n=>{const a=models[n].practical.diagnostic_2025,v=a.checkpoint,st=a.unique_stops;return [names[n],pct(v.precision),pct(v.recall),num(v.FP),`${st.detected}/${st.with_known_horizon_checkpoint}`]})],[335,180,170,220,247],164,360,24);
 text(sl,'Precision: share of alerts that are correct. Recall: share of positive checkpoints alerted.',64,560,1152,65,24);
 text(sl,'Stops found counts distinct stops with known evidence inside the alert horizon.',64,625,1152,34,22,GRAY);
}
{
 const sl=slide(`${names[chosen]}: correct and false alerts`,'Checkpoint confusion in 2025 at the threshold selected using earlier validation years. Distinct-stop detection has a different denominator from checkpoint recall. Repeated positive alerts concern already-counted detected stops.');
 table(sl,[['2025 outcome','Model alerts','Model stays silent'],['Stop inside horizon',num(conf.TP)+' correct alerts',num(conf.FN)+' missed positives'],['No stop inside horizon',num(conf.FP)+' false alerts',num(conf.TN)+' correct silence']],[390,381,381],174,228,27);
 text(sl,`${pct(1-conf.precision)} of alerts are false at threshold ${alert.threshold.toFixed(2)}`,64,444,1152,54,34,BLUE,true);
 text(sl,`${alert.false_alerts_per_driver_race.toFixed(1)} false alerts per eligible driver-race\n${alert.unique_stops.detected} of ${alert.unique_stops.with_known_horizon_checkpoint} distinct stops detected. ${num(alert.unique_stops.repeated_positive_alerts)} repeated positive alerts.`,64,526,1152,98,26);
}
{
 const sl=slide('Calibration and timing windows','Brier score averages squared short-horizon probability error over known binary outcomes. Event coverage is conditional on realized events; predicted mass is mean conditional mass in the selected window. Region width can be open ended at the tail.');
 table(sl,[['Model','Brier score','Median width','Coverage','Predicted mass'],...ids.map(n=>{const v=models[n].practical.validation,w=v.conditional_window_coverage;return [names[n],v.brier_p3.toFixed(4),`${v.window_width.quantiles.median.toFixed(0)} regions`,pct(w.observed),pct(w.expected)]})],[335,190,205,200,222],164,355,23);
 text(sl,'Brier: lower is better. Coverage should agree with the predicted window mass.',64,561,1152,58,25);
 text(sl,'A wide window can cover many stops while giving little timing precision.',64,625,1152,35,24,GRAY);
}
{
 const sl=slide('Recommendation and remaining limits','Exact settings, results, 99-threshold tradeoffs, uncertainty, saved models and provenance are retained. Candidate budget is ten of ten. Future research would require a newly bounded reviewed experiment. No viewer replacement, follow-up merge, deployment or final evaluation is part of this delivery.');
 text(sl,`Retain ${names[chosen]} as the research recommendation`,64,166,1152,110,37,BLUE,true);
 text(sl,`Raw best score: ${names[best]} (${score(best)}).\nThe registered rule accounts for race-level uncertainty.`,64,300,1152,105,29);
 text(sl,'Practical use remains limited by false alerts, missed stops and broad timing windows.',64,438,1152,90,30,INK,true);
 text(sl,'All findings use development races. Earlier unknown outcomes exceed 40%.\nFour tests exhaust the current candidate budget. The viewer remains unchanged.',64,567,1152,82,25,GRAY);
}

const draft=path.join(build,'hypotheses-draft.pptx');await(await PresentationFile.exportPptx(p)).save(draft);
const final=path.join(out,'F1_Hypothesis_Experiments.pptx');
await finalizePresentation({workspaceDir:workspace,candidatePath:draft,finalPath:final,pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],
 requiredNativeTableOwnerSlides:[2,3,4,7,8,9],requiredNativeChartOwnerSlides:[5],explicitTotalSlideCount:10,
 fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
await fs.writeFile(path.join(out,'F1_Hypothesis_Experiments.pdf'),new Uint8Array(await(await p.export({format:'pdf'})).arrayBuffer()));
for(const [i,sl] of p.slides.items.entries())await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await(await p.export({slide:sl,format:'png',scale:1})).arrayBuffer()));
console.log(JSON.stringify({pptx:final,slides:p.slides.items.length}));
