import test from 'node:test';
import assert from 'node:assert/strict';
import { draftKey, loadDraft, saveDraft, reconcilePending, safeURL, rejectedSubmission, restartDraft } from '../src/recovery.mjs';

const memory = () => { const data = new Map(); return { getItem: k => data.get(k), setItem: (k,v) => data.set(k,v), removeItem: k => data.delete(k) }; };
test('drafts are isolated by store, track and activity', () => {
  const storage = memory();
  const key = draftKey('store-a','track-a','activity-a');
  saveDraft(storage,key,{answer:'My reasoning',run_id:'server-run',pending:{run_id:'server-run',context_id:'context-a',answer:'Exact text'}});
  assert.equal(loadDraft(storage,key).pending.answer,'Exact text');
  assert.equal(loadDraft(storage,draftKey('store-b','track-a','activity-a')).answer,'');
});
test('corrupted drafts recover without silently submitting', () => {
  const storage=memory(); storage.setItem('x','not json');
  assert.equal(loadDraft(storage,'x').answer,'');
  storage.setItem('x',JSON.stringify({version:1,answer:'a',pending:{answer:'x'}}));
  assert.equal(loadDraft(storage,'x').pending,null);
});
test('readback only resolves an exact committed run and answer', () => {
  const pending={run_id:'r1',answer:'Original'};
  assert.equal(reconcilePending(pending,[{run_id:'r2',answer:'Original'}]),null);
  assert.equal(reconcilePending(pending,[{run_id:'r1',answer:'Different'}]),null);
  assert.equal(reconcilePending(pending,[{id:'a1',run_id:'r1',answer:'Original'}]).id,'a1');
});
test('source URLs reject executable and credential-bearing schemes', () => {
  assert.equal(safeURL('javascript:alert(1)'),null);
  assert.equal(safeURL('https://name:secret@example.org'),null);
  assert.equal(safeURL('https://example.org/paper'),'https://example.org/paper');
});
test('revoked-context rejection frees the draft without losing the exact answer',()=>{
 const pending={run_id:'old-run',context_id:'revoked',answer:'Exact original answer'};
 assert.equal(rejectedSubmission({status:403}),true);
 assert.equal(rejectedSubmission({status:500}),false);
 assert.equal(rejectedSubmission(new Error('network')),false);
 const result=restartDraft({answer:'other text',pending});
 assert.equal(result.answer,pending.answer);assert.equal(result.pending,null);assert.equal(result.run_id,null);assert.equal(result.previous_submission.run_id,'old-run');
});
