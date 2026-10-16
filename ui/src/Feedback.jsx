import React from 'react';
import {Field,human,DateLabel} from './primitives.jsx';
export function CriterionFields({criteria,results,onChange,disabled=false}) {
 return <fieldset className="hl-criterion-fields"><legend>Check each criterion</legend>{criteria.map((criterion,index)=><div className="hl-criterion" key={index}><p><span>{index+1}.</span> {criterion}</p><Field label={`Criterion ${index+1} outcome`}><select disabled={disabled} value={results[index]?.outcome||'developing'} onChange={e=>onChange(index,'outcome',e.target.value)}><option value="needs-work">Needs another look</option><option value="developing">Developing</option><option value="demonstrated">Demonstrated in this answer</option></select></Field><Field label={`Evidence for criterion ${index+1}`}><textarea disabled={disabled} rows={2} required maxLength={2000} placeholder="Which part of your answer supports this?" value={results[index]?.feedback||''} onChange={e=>onChange(index,'feedback',e.target.value)}/></Field></div>)}</fieldset>;
}
export function AssessmentDetails({assessment}) {
 return <><p>{assessment.feedback}</p>{assessment.criterion_results?.length>0&&<ol className="hl-criterion-feedback">{assessment.criterion_results.map(result=><li key={result.index}><strong>Criterion {result.index+1}: {human(result.outcome)}</strong><p>{result.feedback}</p></li>)}</ol>}{assessment.uncertainty&&<p className="hl-muted">Uncertainty: {assessment.uncertainty}</p>}</>;
}
export function HelpHistory({events=[]}) {
 if(!events.length)return null;
 return <details className="hl-details"><summary>Recorded assistance ({events.length})</summary>{events.map((event,index)=><section className="hl-help-event" key={event.id||index}><strong>{human(event.level)} · {event.origin==='generated'?'Generated':event.origin==='authored'?'Authored':'Recorded'} help</strong><p className="hl-muted">{human(event.author_kind||event.channel)} · <DateLabel value={event.created_at}/></p><p>{event.content||'Help content was not recorded or is unavailable in this view.'}</p></section>)}</details>;
}
