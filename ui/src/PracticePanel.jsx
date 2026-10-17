import React,{useCallback,useEffect,useRef,useState} from 'react';
import {Markdown} from './CourseContent.jsx';
import {practiceDraftKey,readPracticeDraft,writePracticeDraft,practiceTutorMessage} from './practice-draft.mjs';
const labels={correct:'Correct',partial:'Partly correct',retry:'Needs another try'};
function Button({children,primary=false,...props}){return <button className={`lw-button ${primary?'lw-primary':''}`} type="button" {...props}>{children}</button>;}
function localStore(){try{return globalThis.localStorage;}catch{return null;}}
export function LessonTeaching({teaching}){
 if(!teaching)return null;
 return <section className="lw-teaching" aria-label="Lesson outcome"><span className="lw-eyebrow">WHAT YOU’LL BE ABLE TO DO</span><p>{teaching.outcome}</p>{teaching.prerequisites?.length>0&&<details><summary>Before you begin</summary><ul>{teaching.prerequisites.map((item,i)=><li key={i}>{item}</li>)}</ul></details>}</section>;
}
export function PracticePanel({lesson,course,context,scope,action,evaluator,refreshToken,onAskTutor,tutorDisabled}){
 const exercise=lesson.practice;
 const key=practiceDraftKey(scope,context.track_id,lesson);
 const [draft,setDraft]=useState(()=>readPracticeDraft(localStore(),key));
 const [attempts,setAttempts]=useState([]),[error,setError]=useState(''),[loaded,setLoaded]=useState(false),[submitting,setSubmitting]=useState(false),[storageError,setStorageError]=useState(false);
 const requestId=useRef(null),alive=useRef(true),answerBox=useRef(null),feedbackBox=useRef(null),expectFeedback=useRef(false);
 useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
 const refresh=useCallback(async()=>{try{const result=await action('practice_read',{context_id:context.context_id,lesson_key:lesson.key});if(alive.current){setAttempts(result.attempts||[]);setLoaded(true);setError('');}}catch(e){if(alive.current)setError(e.message);}},[action,context.context_id,lesson.key]);
 useEffect(()=>{refresh();},[refresh,refreshToken]);
 const activeHere=evaluator.active?.track_id===context.track_id&&evaluator.active?.lesson_key===lesson.key&&evaluator.active?.lesson_version===(lesson.version||1);
 const running=activeHere&&evaluator.busy;
 useEffect(()=>{if(!running)return;const timer=setInterval(refresh,1500);return()=>clearInterval(timer);},[running,refresh]);
 const latest=attempts.at(-1),pending=attempts.findLast(item=>item.status==='pending');
 const feedback=latest?.status==='completed'?latest:null;
 useEffect(()=>{if(feedback&&expectFeedback.current&&feedbackBox.current?.offsetParent){expectFeedback.current=false;feedbackBox.current.focus({preventScroll:true});feedbackBox.current.scrollIntoView({block:'nearest'});}},[feedback?.id]);
 useEffect(()=>{if(latest&&latest.status!=='pending')requestId.current=null;},[latest?.id,latest?.status]);
 const update=values=>{const next={...draft,...values};setStorageError(!writePracticeDraft(localStore(),key,next));setDraft(next);};
 async function check(){
  if(!draft.answer.trim()||submitting||evaluator.busy||pending)return;
  const payload={answer:draft.answer,hints_used:draft.hints,explanation_shown:draft.revealed};
  const fingerprint=JSON.stringify(payload);
  if(requestId.current?.fingerprint!==fingerprint)requestId.current={fingerprint,id:globalThis.crypto.randomUUID()};
  expectFeedback.current=true;setSubmitting(true);setError('');
  try{await evaluator.check({context,course,lesson,...payload,request_id:requestId.current.id});requestId.current=null;}
  catch(e){if(alive.current)setError(e.message);}
  finally{if(alive.current){setSubmitting(false);await refresh();}}
 }
 async function recover(){setError('');try{if(pending)await evaluator.restore({context,course,lesson,attempt:pending});else await evaluator.reconnect();await refresh();}catch(e){if(alive.current)setError(e.message);}}
 async function stop(){try{await evaluator.stop();await refresh();}catch(e){if(alive.current)setError(e.message);}}
 const retry=()=>{requestId.current=null;update({skipped:false});answerBox.current?.focus();};
 return <section className="lw-practice" aria-label="Lesson practice"><header><div><span className="lw-eyebrow">PUT IT INTO PRACTICE</span><h2>Try it</h2></div><span className="lw-practice-optional">Optional · no score</span></header>
 {draft.skipped?<div className="lw-practice-skipped"><p>Skipped for now. You can return whenever you’re ready.</p><Button onClick={()=>update({skipped:false})}>Open practice</Button></div>:<>
 <Markdown content={exercise.prompt}/>
 <details className="lw-practice-criteria"><summary>What a good answer covers</summary><ul>{exercise.criteria.map((item,i)=><li key={i}>{item}</li>)}</ul></details>
 <label htmlFor="lw-practice-answer">{exercise.kind==='code'?'Your code and explanation':exercise.kind==='project'?'Your implementation or results':'Your answer'}</label>
 <textarea ref={answerBox} id="lw-practice-answer" className={exercise.kind==='code'?'is-code':''} rows={5} maxLength={20000} value={draft.answer} onChange={e=>update({answer:e.target.value})} placeholder={exercise.kind==='code'?'Paste your code and explain your approach…':'Explain your reasoning…'}/>
 <p className="lw-practice-note">{exercise.kind==='explanation'?'Feedback checks your reasoning, not exact wording.':'AI reviews the code or output you share. Code is not executed.'} Your answer is sent to your selected Hermes model when you check it.</p>
 {storageError&&<p role="status" className="lw-practice-note">This device could not save your draft. Copy it before closing Learning.</p>}
 <div className="lw-button-row"><Button primary disabled={!loaded||!draft.answer.trim()||!!pending||evaluator.busy||evaluator.needsReconnect||submitting} onClick={check}>{running||submitting?'Checking answer…':'Check answer'}</Button><Button disabled={draft.hints>=exercise.hints.length} onClick={()=>update({hints:draft.hints+1})}>Hint{draft.hints?` (${draft.hints}/${exercise.hints.length})`:''}</Button><Button disabled={draft.revealed} onClick={()=>update({revealed:true})}>Show explanation</Button><Button onClick={()=>update({skipped:true})}>Skip</Button></div>
 {draft.hints>0&&<div className="lw-practice-hints"><h3>{draft.hints===1?'Hint':'Hints'}</h3>{exercise.hints.slice(0,draft.hints).map((hint,i)=><Markdown key={i} content={hint}/>)}</div>}
 {draft.revealed&&<div className="lw-practice-explanation"><h3>Explanation</h3><Markdown content={exercise.explanation}/></div>}
 </>}
 {(running||pending||(activeHere&&evaluator.needsReconnect))&&<div className="lw-practice-progress" role="status"><p>{running?'Checking your answer. You can keep browsing lessons.':'An answer check is unfinished. Reconnect to check its saved result.'}</p>{running?<Button onClick={stop}>Stop checking</Button>:<Button disabled={evaluator.busy} onClick={recover}>Reconnect answer check</Button>}</div>}
 {(evaluator.busy||evaluator.needsReconnect)&&!activeHere&&<p className="lw-practice-note" role="status">{evaluator.needsReconnect?'Reconnect the previous answer check before starting another.':'Another answer is being checked.'} Your draft stays here.</p>}
 {(error||(activeHere&&evaluator.error))&&<div className="lw-inline-error" role="alert">{error||(activeHere&&evaluator.error)}{!loaded&&<Button onClick={refresh}>Retry loading practice</Button>}</div>}
 {feedback&&<div ref={feedbackBox} tabIndex={-1} className={`lw-practice-feedback is-${feedback.outcome}`} aria-live="polite"><span className="lw-eyebrow">FEEDBACK · AI REVIEW</span><h3>{labels[feedback.outcome]||'Feedback'}</h3><blockquote>{feedback.answer}</blockquote><Markdown content={feedback.feedback}/>{(feedback.hints_used>0||feedback.explanation_shown)&&<p className="lw-practice-note">Completed with {feedback.explanation_shown?'the explanation available':`${feedback.hints_used} hint${feedback.hints_used===1?'':'s'}`}.</p>}<div className="lw-button-row"><Button onClick={retry}>Try again</Button><Button disabled={tutorDisabled} onClick={()=>onAskTutor(practiceTutorMessage(lesson,feedback.answer,feedback.feedback))}>Ask tutor about this</Button></div></div>}
 {latest&&['failed','stopped','stale'].includes(latest.status)&&<p className="lw-practice-note" role="status">{latest.status==='stale'?'This lesson changed. Check a new answer against the updated exercise.':latest.status==='stopped'?'Answer check stopped. Your answer is saved.':'The answer check did not finish. Your answer is saved; you can check it again.'}</p>}
 {attempts.length>1&&<details className="lw-practice-history"><summary>Previous attempts ({attempts.length-1})</summary>{attempts.slice(0,-1).reverse().map((item,i)=><article key={item.id}><h3>Attempt {attempts.length-1-i} · {labels[item.outcome]||item.status}</h3><blockquote>{item.answer}</blockquote>{item.feedback&&<Markdown content={item.feedback}/>}</article>)}</details>}
 {!feedback&&<button className="lw-practice-tutor-link" disabled={tutorDisabled} onClick={()=>onAskTutor(practiceTutorMessage(lesson,draft.answer,''))}>Ask tutor about this</button>}
 </section>;
}
