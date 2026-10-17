import test from 'node:test';
import assert from 'node:assert/strict';
import {practiceDraftKey,readPracticeDraft,writePracticeDraft,practiceTutorMessage} from '../src/practice-draft.mjs';
test('practice drafts are scoped to store, lesson identity and version',()=>{
 const lesson={id:'one',version:1};const first=practiceDraftKey('vps/profile','track',lesson);
 assert.notEqual(first,practiceDraftKey('other','track',lesson));
 assert.notEqual(first,practiceDraftKey('vps/profile','track',{...lesson,version:2}));
 const data=new Map(),storage={getItem:k=>data.get(k),setItem:(k,v)=>data.set(k,v)};
 const draft={answer:'A before B',hints:1,revealed:false,skipped:false};
 assert.equal(writePracticeDraft(storage,first,draft),true);
 assert.deepEqual(readPracticeDraft(storage,first),draft);
 assert.equal(readPracticeDraft(storage,'other').answer,'');
});
test('broken or unavailable storage does not crash practice',()=>{
 assert.equal(readPracticeDraft({getItem:()=>'{bad'},'x').answer,'');
 assert.equal(writePracticeDraft({setItem(){throw Error('quota');}},'x',{}),false);
});
test('explicit tutor handoff includes exercise and answer without evaluation capability',()=>{
 const result=practiceTutorMessage({title:'Ordering',practice:{prompt:'Can B arrive first?',explanation:'Reference'}},'Yes','Correct');
 assert.match(result,/Can B arrive first\?/);assert.match(result,/My answer:\nYes/);assert.match(result,/Practice feedback:\nCorrect/);
 assert.doesNotMatch(result,/Reference|evaluation_token/);
});

test('navigation preserves all five revealed hints supported by a lesson',()=>{
 const storage={getItem:()=>JSON.stringify({answer:'Attempt',hints:5,revealed:false,skipped:false})};
 assert.equal(readPracticeDraft(storage,'key').hints,5);
});
