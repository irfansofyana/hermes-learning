export function draftKey(store, track, activity) {
  return `hermes-learning:draft:v1:${encodeURIComponent(store)}:${encodeURIComponent(track)}:${encodeURIComponent(activity)}`;
}
const blank = () => ({answer:'',run_id:null,context_id:null,pending:null});
export function loadDraft(storage,key) {
  try {
    const value=JSON.parse(storage.getItem(key));
    if(value?.version!==1 || typeof value.answer!=='string') return blank();
    const pending = value.pending && typeof value.pending.run_id==='string' && typeof value.pending.answer==='string' && typeof value.pending.context_id==='string' ? value.pending : null;
    return {...blank(),...value,pending};
  } catch { return blank(); }
}
export function saveDraft(storage,key,value) { storage.setItem(key,JSON.stringify({...value,version:1})); }
export function reconcilePending(pending,attempts) {
  return pending ? attempts.find(a=>a.run_id===pending.run_id && a.answer===pending.answer) || null : null;
}
export function rejectedSubmission(error) {
  return [400,401,403,404,409,422].includes(error?.status);
}
export function restartDraft(draft) {
  return {answer:draft.pending?.answer??draft.answer,run_id:null,context_id:null,pending:null,previous_submission:draft.pending||null};
}
export function safeURL(value) {
  try { const url=new URL(value); return ['http:','https:'].includes(url.protocol) && !url.username && !url.password ? url.href : null; } catch { return null; }
}
