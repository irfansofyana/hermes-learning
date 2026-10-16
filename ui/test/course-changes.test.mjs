import test from 'node:test';
import assert from 'node:assert/strict';
import {describeChanges,changeRequest} from '../src/course-changes.mjs';
const outline=[{key:'first',title:'Basics',goal:'Understand queues'},{key:'second',title:'Workers',goal:'Use concurrency'}];
const course={outline,lessons:[{key:'first',content:'Saved explanation'}],position:{completed:['first']}};
test('proposal preview distinguishes additions, removals, rewrites, and retained lessons',()=>{
 const result=describeChanges(course,{mode:'revise',outline:[outline[0],{key:'project',title:'Project',goal:'Build it'}],lessons:[{lesson_key:'first',content:'New explanation'}]});
 assert.deepEqual(result.rows.map(row=>[row.key,row.status]),[['first','Rewrite'],['project','New']]);
 assert.deepEqual(result.removed.map(row=>row.key),['second']);
 assert.equal(result.resetProgress,false);
});
test('extension preserves earlier lessons and regenerate always replaces them',()=>{
 const extended=describeChanges(course,{mode:'extend',outline:[...outline,{key:'project',title:'Project',goal:'Build it'}],lessons:[]});
 assert.deepEqual(extended.rows.map(row=>row.status),['Unchanged','Unchanged','New']);
 assert.equal(describeChanges(course,{mode:'regenerate',outline,lessons:[{key:'first'}]}).rows[0].status,'Rewrite');
 assert.equal(describeChanges(course,{mode:'regenerate',outline,lessons:[]}).resetProgress,true);
});
test('edit requests keep revision and lesson identity out of visible prose',()=>{
 const request=changeRequest('lesson','Use my queue project', {key:'first',title:'Basics'});
 assert.equal(request.mode,'revise');assert.equal(request.target,'lesson');assert.equal(request.lesson_key,'first');assert.match(request.message,/Basics/);assert.match(request.message,/Use my queue project/);
 assert.throws(()=>changeRequest('lesson','Make it practical',null),/Choose a lesson/);
 assert.throws(()=>changeRequest('extend','   ',null),/Describe/);
});
