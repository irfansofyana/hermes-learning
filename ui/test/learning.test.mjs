import test from 'node:test';
import assert from 'node:assert/strict';
import {readSourceFile,visibleSteps,weakestOutcome,tutorPrompt,tutorResumeCommand,SOURCE_MAX_BYTES} from '../src/learning.mjs';
const file=(name,text)=>{const bytes=typeof text==='string'?new TextEncoder().encode(text):text;return {name,size:bytes.byteLength,arrayBuffer:async()=>bytes.buffer};};
test('local source import preserves selected UTF-8 text and a visible file locator',async()=>{
 const input='## Retry\n\nAn idempotency key → one effect.\n';
 assert.deepEqual(await readSourceFile(file('retry.md',input)),{title:'retry.md',locator:'File: retry.md',excerpt:input,kind:'notes'});
 assert.equal((await readSourceFile(file('retry.py','print("hello")'))).kind,'repository');
});
test('local source import rejects binary, unsupported, empty, oversized and malformed UTF-8 files',async()=>{
 for(const input of [file('paper.pdf','text'),file('x.txt',''),file('x.txt','a\0b'),file('x.txt',new Uint8Array([0xc3,0x28])),file('x.md','a'.repeat(50001)),file('x.py','a'.repeat(SOURCE_MAX_BYTES+1))]) await assert.rejects(readSourceFile(input));
});
test('visual stepping never exposes withheld steps including a zero-step gate',()=>{
 const steps=[{label:'question'},{label:'answer'}];
 assert.deepEqual(visibleSteps({steps,visible_steps:1}),[steps[0]]);
 assert.deepEqual(visibleSteps({steps,visible_steps:0}),[]);
 assert.deepEqual(visibleSteps({steps}),steps);
});
test('criterion outcome reflects the weakest recorded evidence',()=>{
 assert.equal(weakestOutcome([{outcome:'demonstrated'},{outcome:'needs-work'}]),'needs-work');
 assert.equal(weakestOutcome([{outcome:'demonstrated'},{outcome:'developing'}]),'developing');
});
test('pending answer handoff targets exact evidence and keeps learner answer out of prompt',()=>{
 const prompt=tutorPrompt({id:'track-1',title:'Retries',status:'active'},{kind:'assessment',activity_id:'activity-1',attempt_id:'attempt-1'});
 assert.match(prompt,/Activity: activity-1\nAttempt: attempt-1/);
 assert.match(prompt,/criterion-level feedback/);
 assert.match(prompt,/not an answer to an activity/);
 assert.equal(prompt.includes('/learning-track'),false);
 assert.equal(tutorResumeCommand({id:'track-1'}),'/learning-track resume track-1');
});
