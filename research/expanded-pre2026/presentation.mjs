import fs from 'node:fs/promises';
import path from 'node:path';
import { Presentation, PresentationFile } from '@oai/artifact-tool';
import { finalizePresentation } from '/root/.codex/skills/builtins/presentations/container_tools/artifact_tool_utils.mjs';
const workspaceDir='/workspace/scratch/90628bafa4f3';
const out=path.join(workspaceDir,'output');
const build=path.join(workspaceDir,'deck_build');
const presentation=Presentation.create({slideSize:{width:1280,height:720}});
const font='DejaVu Sans';
const navy='#142B44', ink='#24384D', muted='#526171';
function txt(slide,text,x,y,w,h,size=28,bold=false,color=ink) {
 const s=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{style:'solid',fill:'none',width:0}});
 s.text=text;s.text.style={fontSize:size,typeface:font,color,bold,insets:0,verticalAlignment:'top',wrap:'square',autoFit:'none'};return s;
}
function slide(title,note='') {
 const s=presentation.slides.add();s.background.fill='#FFFFFF';
 txt(s,title,72,54,1136,90,44,true,navy);
 s.speakerNotes.text=note+'\nSources: https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/pull/56 and research/expanded-pre2026/REPORT.md. Saved experiment: PR #55, research/model-comparison/REPORT.md.';
 return s;
}
function table(s,values,widths,y=174,height=300,size=26){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:72,top:y,width:1136,height,columnWidths:widths,values});
 t.borders.assign({style:'solid',fill:'#D8DEE5',width:1});
 t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({textStyle:{fontSize:size,typeface:font,color:ink},margins:{left:14,right:12,top:14,bottom:12},anchor:'center'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?navy:(r%2?'#F2F5F8':'#FFFFFF');
  cell.text.style={fontSize:size,typeface:font,color:r===0?'#FFFFFF':ink,bold:r===0};
 }
 return t;
}
const evidence=path.join(workspaceDir,'f1-pit-predictor-dataset/research/expanded-pre2026/evaluation');
const r=JSON.parse(await fs.readFile(path.join(evidence,'summary.json'),'utf8'));
const names={B0:'Laps ahead',B1:'Original tyre model',PERCENT_AHEAD:'Percentage ahead',PERCENT_PROGRESS:'Race progress',TYRE_RIDGE:'Stable tyre model'};
const chosen=r.selected,p=r.practical[chosen],b=r.practical.B0,d=p.diagnostic_2025,bc=b.diagnostic_2025.checkpoint,dc=d.checkpoint;
const pct=x=>x==null?'Undefined':`${(100*x).toFixed(1)}%`,num=x=>x.toLocaleString('en-US');
const w=p.validation.window_width,cov=p.validation.conditional_window_coverage;
{
 const s=slide('Pit prediction results','Development under approved archive assumptions. The registered rule uses pooled log score, then prefers a simpler procedure within one race-level standard error. No 2026 source or outcome was opened.');
 txt(s,`${names[chosen]} wins the registered comparison`,72,185,1136,110,39,true);
 txt(s,`Mean validation log score: ${r.models[chosen].mean_log_score.toFixed(3)}\nLap baseline: ${r.models.B0.mean_log_score.toFixed(3)}. Lower is better.`,72,330,1136,115,31);
 txt(s,`2025 alerts: ${pct(dc.precision)} precision and ${pct(dc.recall)} recall.\nThese development results still contain many false alerts.`,72,515,1136,105,28,false,muted);
}
{
 const s=slide('Chronological data split','Each fold trains on every admitted earlier race. No random split of checkpoints or drivers. All133races enter the final refit after selection. 2022archives unavailable.');
 table(s,[['Validation season','Earlier training races','Validation races'],['2019','18','19'],['2020','37','12'],['2021','49','16'],['2023','65','21'],['2024','86','23'],['2025','109','24']],[450,385,301],163,385,26);
 txt(s,'115 validation races. 2018 supplies the initial training data.\nAfter selection, the final fit uses all 133 admitted races.',72,585,1136,94,27);
}
{
 const s=slide('Data quality and source limits','173 sessions audited.133admitted=94older+39raceday.40excluded:22unavailable2022,13counter,2roster,1lifecycle,2unsupported2018.109CSVfiles:104race+5overlappingseasonexports. None used for training. OlderRA1–3/5/6, race-dayRA1–4.');
 table(s,[['Audit result','Count','Treatment'],['Calendar sessions checked','173','Every session recorded'],['Races admitted','133','Raw streams only'],['Races excluded','40','Missing or incompatible'],['Legacy CSV files','109','Quality checks only']],[485,190,461],174,295,26);
 txt(s,'39,065 eligible outcomes remain unknown. They never become negatives.\nFeatures use information available at each checkpoint.',72,510,1136,94,27);
 txt(s,'Older rewritten archives rely on approved timing and version assumptions.\nIndependent checks cannot prove every historical version.',72,624,1136,70,23,false,muted);
}
{
 const s=slide('Model comparison','Four supported procedures share the complete resolvable cohort. Original B1 fails its fitting rules and only supplies partial omission fallback. Ridge penalty0.001 fixed before validation. Python3.12 NumPy2.3.5 SciPy1.17.0.');
 const rows=[['Model','Mean log score','Forecasts / eligible']];
 for(const id of ['B0','PERCENT_AHEAD','PERCENT_PROGRESS','TYRE_RIDGE','B1'])rows.push([names[id],r.models[id].fitting_failures.length?'Unsupported':r.models[id].mean_log_score.toFixed(4),`${num(r.models[id].forecast_count)} / ${num(r.models[id].eligible)}`]);
 table(s,rows,[455,280,401],167,340,25);
 txt(s,'Tyre features use age and compound known at the checkpoint.\nThe stable tyre candidate uses a fixed penalty to support fitting.',72,548,1136,88,26);
 txt(s,'The original tyre model still fails. Partial fallback cannot win selection.',72,653,1136,35,22,false,muted);
}
{
 const s=slide('2025 alerts and confusion matrix','Thresholds maximizeF1 on0.01–0.99grid through2024only, tieshighest. Exploratory due earlier2025exposure. R0currentinlapaftercheckpoint,R1,R2. Shortgridsincludeopenfinalregion. Knowncheckpointcounts only.');
 table(s,[['Known checkpoints','Lap baseline',names[chosen]],['Correct alerts',num(bc.TP),num(dc.TP)],['False alerts',num(bc.FP),num(dc.FP)],['Missed positive checkpoints',num(bc.FN),num(dc.FN)],['Correct no-alert checkpoints',num(bc.TN),num(dc.TN)],['Precision / recall',`${pct(bc.precision)} / ${pct(bc.recall)}`,`${pct(dc.precision)} / ${pct(dc.recall)}`]],[490,323,323],157,355,24);
 txt(s,`Alert threshold: ${d.threshold.toFixed(2)}. Always alerting gives ${pct(dc.prevalence)} precision.\n${num(dc.unknown_binary)} unknown outcomes stay outside this matrix.`,72,548,1136,85,26);
 txt(s,'Horizon: current in-lap after the checkpoint and next two canonical regions.\nA short grid can include the open final region. Several alerts can refer to one stop.',72,642,1136,64,21,false,muted);
}
{
 const s=slide('Pit windows and identifiable stops','Conditional event coverage across validation uses window/v1 and actual predicted conditional mass. Region count measures width. Open tail has no finite lap upper bound. 2025event_ref deduplication counts each identifiable known-horizon stop once.');
 table(s,[['Window measure across validation','Selected model'],['Actual event coverage',pct(cov.observed)],['Mean predicted coverage',pct(cov.expected)],['Median width',`${w.quantiles.median.toFixed(0)} regions`],['Windows with open final region',pct(w.open_ended_share)]],[790,346],171,300,26);
 txt(s,`In 2025, at least one alert precedes ${num(d.unique_stops.detected)} of\n${num(d.unique_stops.with_known_horizon_checkpoint)} identifiable stops. Each stop counts once.`,72,514,1136,92,28);
 txt(s,'Wide windows catch more stops with less precise timing.\nThe open final region has no finite upper limit in laps.',72,628,1136,70,23,false,muted);
}
{
 const s=slide('Probability calibration and uncertainty','Reliability groups sort forecast probabilities. Brier score uses known binary outcomes. CR2+t, Webb9999seed5302026 and leave-one-race-out group checkpoints by race. No calibration correction fitted.');
 const cal=p.validation.calibration_p3,high=cal[cal.length-1];
 table(s,[['Probability check','Predicted','Observed'],['Highest alert-probability group',pct(high.predicted),pct(high.observed)],['Selected model Brier score',p.validation.brier_p3.toFixed(4),'Lower is better'],['Lap baseline Brier score',b.validation.brier_p3.toFixed(4),'Lower is better']],[620,258,258],177,267,25);
 const diff=r.pairs[`B0 vs ${chosen}`]?.difference_a_minus_b;
 txt(s,diff?`Log-score gain over B0: ${diff.mean.toFixed(3)}\n95% interval by race: ${diff.cr2_95[0].toFixed(3)} to ${diff.cr2_95[1].toFixed(3)}`:'The baseline wins the registered simplicity rule.',72,490,1136,93,29);
 txt(s,'Uncertainty groups checkpoints by race. Unknown outcomes remain excluded.\nHistorical archive assumptions limit what the comparison can establish.',72,617,1136,77,24,false,muted);
}
{
 const s=slide('Frozen procedure and final-test boundary','Selection freeze precedes all133refit. Final threshold uses all chronological validation and has in-sample pooled selection diagnostics. Earlier-threshold2025diagnostic is separate. Final resolution-run and F2fixedmetadata-list gates remain. No EvaluationLock claim.');
 txt(s,'Model selection and refit complete',72,175,1136,50,33,true);
 txt(s,`${names[chosen]} and the lap baseline now have saved fits using\nall 133 admitted pre-2026 races. Final alert threshold: ${p.final_threshold.threshold.toFixed(2)}.`,72,250,1136,125,29);
 txt(s,'2026 remains reserved for final testing',72,420,1136,50,33,true);
 txt(s,'Final testing still requires the existing resolution, fixed-list and lock gates.\nNo 2026 outcomes entered model development or threshold selection.',72,491,1136,102,27);
 txt(s,'The current viewer stays in place. No merge or deployment.',72,642,1136,40,25,false,muted);
}
await fs.mkdir(out,{recursive:true});
const candidatePath=path.join(build,'expanded-candidate.pptx');await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
const finalPath=path.join(out,'F1_Issue_53_Expanded_Report.pptx');
await finalizePresentation({workspaceDir,candidatePath,finalPath,pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,integrityValidatorPath:'/root/.codex/skills/builtins/presentations/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:'/root/.codex/skills/builtins/presentations/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[2,3,4,5,6,7].flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:[2,3,4,5,6,7],fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:path.join(build,'expanded-validation.json')});
for(let i=0;i<presentation.slides.items.length;i++){const b=await presentation.export({slide:presentation.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(build,`expanded-slide-${i+1}.png`),new Uint8Array(await b.arrayBuffer()));}
console.log(finalPath);
