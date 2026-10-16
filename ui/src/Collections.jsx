import React,{useCallback,useEffect,useState} from 'react';
import {Button,Field,DateLabel,human,Empty,Modal} from './primitives.jsx';
import {Icon} from './icons.jsx';
import {safeURL} from './recovery.mjs';

export function Sources({sources=[],request,onAdd,canWrite,busy}) {
 const [selected,setSelected]=useState(null),[reading,setReading]=useState(null),[error,setError]=useState(''),[loading,setLoading]=useState(false);
 const source=sources.find(item=>item.id===selected);
 useEffect(()=>{
  let cancelled=false;setReading(null);setError('');
  if(!source){setLoading(false);return;}
  setLoading(true);
  request(`/source/${encodeURIComponent(source.id)}`).then(result=>{if(!cancelled)setReading(result.source);}).catch(e=>{if(!cancelled)setError(e.message||'Could not load this source.');}).finally(()=>{if(!cancelled)setLoading(false);});
  return()=>{cancelled=true;};
 },[source?.id,request]);
 const add=<Button icon="plus" onClick={onAdd} disabled={!canWrite||busy}>Add source</Button>;
 return <section className="hl-collection" aria-label="Sources">
  <div className="hl-toolbar"><div><h2 className="hl-section-heading">Your sources</h2><p className="hl-muted">Curated references and text you chose to attach.</p></div>{add}</div>
  {!canWrite&&<p className="hl-muted">Resume this track to attach a source.</p>}
  {!sources.length?<Empty title="Give your learning a reference">Add a link, reading notes, or selected text. A link alone does not import its contents.</Empty>:sources.map(item=><section className="hl-list-row" key={item.id}>
   <div><h3>{item.title}</h3><p className="hl-muted">{human(item.kind)} · {human(item.sharing)} · {human(item.verification||'Verification not recorded')}</p>{item.locator&&<p className="hl-muted">{item.locator}</p>}</div>
   <Button icon="file" onClick={()=>setSelected(item.id)} aria-pressed={selected===item.id}>Read source</Button>
  </section>)}
  {source&&<section className="hl-source-reading" aria-label={`Source: ${source.title}`} aria-busy={loading}>
   <div className="hl-toolbar"><h3>{source.title}</h3><Button onClick={()=>setSelected(null)}>Close reading</Button></div>
   <p className="hl-muted">Model sharing: {human(source.sharing)}. Your attached text remains readable here.</p>
   {safeURL(source.url)&&<a href={safeURL(source.url)} target="_blank" rel="noopener noreferrer"><Icon name="link"/> Open original source</a>}
   {loading&&<p role="status">Loading source…</p>}{error&&<p className="hl-callout" role="alert">{error}</p>}
   {reading&&<p style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{reading.excerpt||'No text is attached. This source currently contains reference metadata only.'}</p>}
  </section>}
 </section>;
}

export function Evidence({attempts=[],assessments=[],activities=[],workspace,onChat}) {
 const [editing,setEditing]=useState(null),[text,setText]=useState(''),[outcome,setOutcome]=useState('developing'),[error,setError]=useState('');
 const close=useCallback(()=>setEditing(null),[]);
 const editable=attempt=>workspace.connected&&workspace.context?.track_id===attempt.track_id;
 function open(mode,assessment,attempt){setEditing({mode,assessment,attempt});setText(mode==='correct'?assessment.feedback:'');setOutcome(assessment.outcome||'developing');setError('');}
 async function save(event){
  event.preventDefault();if(!editing||!editable(editing.attempt))return;
  try{
   if(editing.mode==='dispute')await workspace.act('dispute',{assessment_id:editing.assessment.id,reason:text});
   else await workspace.act('assess',{attempt_id:editing.attempt.id,method:'self',feedback:text,outcome,supersedes:editing.assessment.id});
   close();
  }catch(e){setError(e.message||'Could not save this change.');}
 }
 if(!attempts.length)return <Empty title="Evidence starts with an attempt">Your submitted answers and their assessments will appear here. Drafts remain in the practice workspace.</Empty>;
 return <section className="hl-collection" aria-label="Learning evidence">
  <h2 className="hl-section-heading">Your learning evidence</h2><p className="hl-muted">Answers, assistance, and assessments stay together. Self and agent assessments are recorded separately.</p>
  {[...attempts].sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at))).map(attempt=>{
   const activity=activities.find(item=>item.id===attempt.activity_id);
   const feedback=assessments.filter(item=>item.attempt_id===attempt.id);
   return <section className="hl-evidence-item" key={attempt.id}>
    <h3>{activity?.title||'Recorded activity'}</h3>
    <p className="hl-muted"><DateLabel value={attempt.created_at}/> · Activity version {attempt.activity_version??activity?.version??'not recorded'} · {human(attempt.channel)} · Assistance: {human(attempt.assistance||'unknown')}</p>
    <p style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{attempt.answer}</p>
    {!feedback.length&&<p className="hl-callout">Awaiting assessment. Submission alone does not demonstrate understanding.</p>}
    {['self','agent'].map(method=>{
     const group=feedback.filter(item=>item.method===method);
     if(!group.length)return null;
     return <section key={method} aria-label={`${human(method)} assessments`}>
      <h4>{method==='self'?'Self-assessments':'Agent assessments'}</h4>
      {group.map(assessment=>{
       const superseded=feedback.some(item=>item.supersedes===assessment.id);
       return <section className="hl-assessment" key={assessment.id}>
        <p><strong>{human(assessment.outcome)}</strong> · <DateLabel value={assessment.created_at}/>{superseded?' · Superseded':''}{assessment.supersedes?' · Correction':''}</p>
        <p style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{assessment.feedback}</p>
        {(workspace.state?.disputes||[]).filter(item=>item.assessment_id===assessment.id).map(dispute=><div className="hl-callout" key={dispute.id}><strong>Assessment disputed</strong> · <DateLabel value={dispute.created_at}/><p style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{dispute.reason}</p></div>)}
        <div className="hl-toolbar"><Button onClick={()=>open('dispute',assessment,attempt)} disabled={!editable(attempt)||workspace.busy}>Dispute assessment</Button>
         {method==='self'&&!superseded&&<Button onClick={()=>open('correct',assessment,attempt)} disabled={!editable(attempt)||workspace.busy}>Correct self-assessment</Button>}</div>
       </section>;
      })}
     </section>;
    })}
    {!editable(attempt)&&feedback.length>0&&<p className="hl-muted">Resume this track to dispute or correct an assessment.</p>}
    {onChat&&<Button icon="chat" onClick={()=>onChat(attempt)}>Prepare chat handoff</Button>}
   </section>;
  })}
  {editing&&<Modal title={editing.mode==='dispute'?'Dispute assessment':'Correct self-assessment'} onClose={close}>
   <form onSubmit={save}>
    <p className="hl-muted">The original assessment remains in your evidence history.</p>
    {editing.mode==='correct'&&<Field label="Outcome"><select value={outcome} onChange={e=>setOutcome(e.target.value)}><option value="needs-work">Needs work</option><option value="developing">Developing</option><option value="demonstrated">Demonstrated</option></select></Field>}
    <Field label={editing.mode==='dispute'?'Reason for dispute':'Updated feedback'}><textarea required maxLength={editing.mode==='dispute'?4000:20000} rows={5} value={text} onChange={e=>setText(e.target.value)}/></Field>
    {error&&<p role="alert" className="hl-callout">{error}</p>}
    {!editable(editing.attempt)&&<p role="alert">Resume this track before saving.</p>}
    <div className="hl-toolbar"><Button type="button" onClick={close}>Cancel</Button><Button type="submit" kind="primary" disabled={workspace.busy||!text.trim()||!editable(editing.attempt)}>Save {editing.mode==='dispute'?'dispute':'correction'}</Button></div>
   </form>
  </Modal>}
 </section>;
}

export function Reviews({state,workspace,onOpen}) {
 const reviews=[...(state?.reviews||[])].sort((a,b)=>String(a.due_at).localeCompare(String(b.due_at)));
 async function act(action,params){try{await workspace.act(action,params);}catch(e){workspace.setError?.(e.message||'Could not update this review.');}}
 return <section className="hl-collection" aria-label="Review queue">
  <h1 className="hl-page-title">Return to what matters.</h1><p className="hl-page-intro">Review dates come from recorded assessments or your own scheduling choices.</p>
  {!reviews.length?<Empty title="No reviews scheduled">Assess a submitted attempt to create its next review.</Empty>:reviews.map(review=>{
   const track=state.tracks.find(item=>item.id===review.track_id),activity=state.activities.find(item=>item.id===review.activity_id);
   const active=workspace.context?.track_id===review.track_id;
   const due=new Date(review.due_at),valid=Number.isFinite(due.getTime());
   const overdue=valid&&due.getTime()<=Date.now();
   return <section className="hl-review-item" key={review.id}>
    <p className="hl-muted">{track?.title||'Recorded track'} · {overdue?'Due now':'Scheduled'} · <DateLabel value={review.due_at}/></p>
    <h2>{activity?.title||'Recorded activity'}</h2><p>{review.reason}</p>
    <div className="hl-toolbar"><Button icon="arrow" onClick={()=>onOpen(review.track_id,review.activity_id)}>Open activity</Button>
     {active?<Button icon="clock" disabled={workspace.busy||!workspace.connected||!valid} onClick={()=>act('review',{review_id:review.id,due_at:new Date(Math.max(Date.now(),due.getTime())+86400000).toISOString()})}>Defer one day</Button>:<Button icon="play" disabled={workspace.busy||!workspace.connected} onClick={()=>act('resume',{track_id:review.track_id})}>Resume this track</Button>}
    </div>
   </section>;
  })}
 </section>;
}

export function Recommendations({recommendations=[],workspace,onAttach}) {
 const [error,setError]=useState('');
 async function decide(recommendation,status){
  setError('');
  try{await workspace.act('recommendation_decide',{recommendation_id:recommendation.id,status});}
  catch(e){setError(e.message||'Could not save your decision.');}
 }
 return <section className="hl-collection" aria-label="Source recommendations">
  <h2 className="hl-section-heading">Suggested sources</h2>
  <p className="hl-muted">Choose which references to use. Accepting a suggestion does not retrieve or attach its contents.</p>
  {error&&<p className="hl-callout" role="alert">{error}</p>}
  {!recommendations.length?<p className="hl-muted">No source suggestions yet.</p>:recommendations.map(recommendation=>{
   const canWrite=workspace.connected&&workspace.context?.track_id===recommendation.track_id;
   const url=safeURL(recommendation.url);
   return <section className="hl-list-row" key={recommendation.id}>
    <div><h3>{recommendation.title}</h3>
     <p className="hl-muted">{human(recommendation.status)} · {human(recommendation.verification||'unverified')}</p>
     {url&&<a href={url} target="_blank" rel="noopener noreferrer" style={{overflowWrap:'anywhere'}}>{recommendation.url}</a>}
     <p style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{recommendation.reason}</p>
     {recommendation.locator&&<p className="hl-muted">Location: {recommendation.locator}</p>}
     {!!recommendation.prerequisites?.length&&<div><strong>Prerequisites</strong><ul>{recommendation.prerequisites.map((item,index)=><li key={index}>{item}</li>)}</ul></div>}
     {!canWrite&&<p className="hl-muted">Resume this track to record your decision or attach text.</p>}
     <div className="hl-toolbar">
      {recommendation.status!=='accepted'&&<Button icon="check" disabled={!canWrite||workspace.busy} onClick={()=>decide(recommendation,'accepted')}>Accept</Button>}
      {recommendation.status!=='declined'&&<Button disabled={!canWrite||workspace.busy} onClick={()=>decide(recommendation,'declined')}>Decline</Button>}
      {recommendation.status==='accepted'&&<Button icon="plus" disabled={!canWrite||workspace.busy} onClick={()=>onAttach(recommendation)}>Attach selected text</Button>}
     </div>
    </div>
   </section>;
  })}
 </section>;
}
