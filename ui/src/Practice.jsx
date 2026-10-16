import React,{useState,useEffect} from 'react';
import {Button,Field,human} from './primitives.jsx';
import {draftKey,loadDraft,saveDraft,reconcilePending,rejectedSubmission,restartDraft} from './recovery.mjs';
export function Practice({activity,track,workspace,onUpdated,onChat}) {
 const {state,context,act,busy,connected,setError}=workspace;
 const key=draftKey(state.store_id,track.id,activity.id);
 const [draft,setDraft]=useState(()=>loadDraft(localStorage,key));
 const [help,setHelp]=useState(''),[feedback,setFeedback]=useState(''),[outcome,setOutcome]=useState('developing'),[storageError,setStorageError]=useState('');
 const active=context?.track_id===track.id, attempts=state.attempts.filter(a=>a.activity_id===activity.id);
 const saved=attempts.find(a=>a.run_id===draft.run_id), resolved=reconcilePending(draft.pending,attempts);
 const locked=!!saved||!!draft.pending;
 function change(value){setDraft(previous=>{const next={...previous,...value};try{saveDraft(localStorage,key,next);setStorageError('');}catch{setStorageError('Local storage is unavailable. Keep this page open to retain your draft.');}return next;});}
 useEffect(()=>{if(resolved)change({pending:null});},[resolved?.id]);
 async function run(){if(draft.run_id && draft.context_id===context?.context_id)return draft.run_id;const value=await act('run',{activity_id:activity.id});change({run_id:value.run_id,context_id:context.context_id});return value.run_id;}
 async function submit(){let payload=draft.pending;try{const run_id=payload?.run_id||await run();payload=payload||{context_id:context.context_id,run_id,answer:draft.answer};change({pending:payload});await act('submit',payload);change({pending:null});onUpdated();}catch(e){if(payload&&rejectedSubmission(e))change(restartDraft({...draft,pending:payload}));/* Network failures retain exact identity; definitive rejections keep an editable draft. */}}
 async function hint(level){try{const run_id=await run();const result=await act('help',{run_id,level});setHelp(result.text||result.content||result.help?.text||result.help?.content||result.hint||JSON.stringify(result));onUpdated();}catch{}}
 async function newAttempt(){try{const result=await act('run',{activity_id:activity.id});change({answer:'',run_id:result.run_id,context_id:context.context_id,pending:null});setHelp('');onUpdated();}catch{}}
 async function assess(e){e.preventDefault();try{await act('assess',{attempt_id:saved.id,method:'self',feedback,outcome});setFeedback('');onUpdated();}catch{}}
 const assessments=saved?state.assessments.filter(a=>a.attempt_id===saved.id):[];
 return <aside className="hl-practice" aria-label="Practice"><h2>{saved?'Your answer':'Your prediction'}</h2><p className="hl-practice-prompt">{activity.prompt}</p>
 {!active&&<div className="hl-callout"><strong>Read at your own pace.</strong><p>Resume tracked learning when you want to save an answer.</p><Button kind="primary" disabled={busy||!connected} onClick={()=>act('resume',{track_id:track.id}).catch(()=>{})}>Resume tracked learning</Button></div>}
 <label className="hl-sr" htmlFor="learning-answer">Your answer</label>
 <textarea id="learning-answer" className="hl-answer" placeholder="Walk through your reasoning…" rows={8} value={draft.answer} maxLength={8000} disabled={locked||busy} onChange={e=>change({answer:e.target.value})}/>
 <div className="hl-draft-status"><span>{saved?'Saved · awaiting or recorded assessment':draft.pending?'Delivery uncertain · exact answer retained':'Draft · not submitted'}</span>{draft.answer&&!locked&&<button className="hl-text-btn" onClick={()=>change({answer:''})}>Clear</button>}</div>
 {storageError&&<p role="status" className="hl-warning">{storageError}</p>}
 {draft.pending&&<p className="hl-warning">Check saved evidence or retry this exact answer. Starting a new attempt first could duplicate your work.</p>}
 {!saved&&<Button kind="primary wide" disabled={!active||busy||!connected||!draft.answer.trim()||(draft.pending&&draft.pending.context_id!==context?.context_id)} onClick={submit}>{draft.pending?'Retry same answer':'Submit answer'}</Button>}
 {draft.pending&&draft.pending.context_id!==context?.context_id&&<p className="hl-muted">This answer belongs to an earlier workspace session. Refresh to check whether it was saved. Keep this draft until you resolve it in Evidence.</p>}
 {draft.pending&&<details className="hl-details"><summary>Recover this draft in a new attempt</summary><p>First check Evidence for the earlier answer. This deliberately abandons its retry identity and may create another answer if the earlier delivery succeeded. The original text will be kept.</p><Button disabled={!active||busy||!connected} onClick={()=>{change(restartDraft(draft));setHelp('');}}>Keep text and start a new attempt</Button></details>}
 {!saved&&<Button kind="wide" disabled={!active||busy||!connected||!!draft.pending} onClick={()=>hint('nudge')}>Give me a hint</Button>}
 {help&&<div className="hl-callout"><strong>Recorded help</strong><p>{help}</p><Button kind="text" disabled={busy||!active} onClick={()=>hint('targeted-hint')}>A more specific hint</Button></div>}
 {!saved&&<details className="hl-details"><summary>Prefer to see the explanation?</summary><p>Revealing the solution records the help you used.</p><Button disabled={!active||busy||!!draft.pending} onClick={()=>hint('full-solution-shown')}>Reveal solution</Button></details>}
 {saved?<><p className="hl-muted">{human(saved.channel)} · Assistance: {human(saved.assistance)}</p><Button kind="wide" disabled={!active||busy||!connected} onClick={newAttempt}>Start a new attempt</Button>
 {activity.criteria&&<section className="hl-self-check"><h3>Check your reasoning</h3><ul>{activity.criteria.map((c,i)=><li key={i}>{c}</li>)}</ul>{activity.solution&&<details className="hl-details"><summary>Reference explanation</summary><p>{activity.solution}</p></details>}
 <form onSubmit={assess}><Field label="Your assessment"><select value={outcome} onChange={e=>setOutcome(e.target.value)}><option value="needs-work">Needs another look</option><option value="developing">Developing</option><option value="demonstrated">Demonstrated in this answer</option></select></Field><Field label="What supports your assessment?"><textarea rows={3} value={feedback} onChange={e=>setFeedback(e.target.value)} required maxLength={12000}/></Field><Button kind="primary" disabled={!active||busy||!feedback.trim()}>Save self-assessment</Button></form></section>}
 {assessments.map(a=><div className="hl-assessment" key={a.id}><strong>{human(a.method)} · {human(a.outcome)}</strong><p>{a.feedback}</p></div>)}</>:<p className="hl-muted hl-save-note">Your answer is saved before assessment. Review it yourself or continue in chat.</p>}
 <Button icon="chat" kind="text" onClick={onChat}>Continue with your tutor</Button>
 </aside>;
}
