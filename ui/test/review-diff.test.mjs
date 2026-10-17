import test from 'node:test';
import assert from 'node:assert/strict';
import {textDiff,reviewEntries,lessonSections} from '../src/review-diff.mjs';
const outline=[{key:'a',title:'Events',goal:'Follow events'},{key:'b',title:'Consumers',goal:'Read events'}];
const course={outline,lessons:[{key:'a',content:'Old explanation',practice:{prompt:'Explain',hints:['Hint'],criteria:['Correct'],explanation:'Answer'}}]};
test('diff reconstructs both inputs exactly, including whitespace and final newline',()=>{
 for(const [before,after] of [['one\ntwo\n','one\nthree\n'],['a','a\n'],['','new'],['gone',''],[' same \n',' same\n'],['重复 😀','重复 👍']]){
  const result=textDiff(before,after),rows=result.groups.flatMap(g=>g.rows);
  for(const row of rows)if(row.words)assert.equal(row.words.map(w=>w.text).join(''),row.text);
  assert.equal(rows.filter(r=>r.kind!=='added').map(r=>r.text).join(''),before);
  assert.equal(rows.filter(r=>r.kind!=='removed').map(r=>r.text).join(''),after);
 }
});
test('long unchanged sections collapse but retain nearby context',()=>{
 const before=Array.from({length:30},(_,i)=>`Line ${i}\n`).join('');
 const result=textDiff(before,before.replace('Line 15','Changed 15'));
 assert.ok(result.groups.some(g=>g.collapsed&&g.rows.length>5));
 assert.equal(result.added,1);assert.equal(result.removed,1);
 assert.ok(result.groups.flatMap(g=>g.rows).some(r=>r.words?.some(w=>w.changed)));
});
test('large unrelated rewrites use a bounded full replacement fallback',()=>{
 const result=textDiff('a\n'.repeat(4000),'b\n'.repeat(4000),{maxEditLength:1});
 assert.equal(result.coarse,true);assert.equal(result.added,4000);assert.equal(result.removed,4000);
});
test('roadmap identity keeps renames and moves together and includes removed and new lessons',()=>{
 const result=reviewEntries(course,{mode:'revise',outline:[{...outline[1],title:'Groups'}, {key:'c',title:'Project',goal:'Build'}],lessons:[]});
 assert.deepEqual(result.map(r=>r.key),['b','c','a']);
 assert.ok(result[0].labels.includes('Renamed'));assert.ok(result[0].labels.includes('Moved'));
 assert.ok(result[1].labels.includes('Added'));assert.ok(result[2].labels.includes('Removed'));
 assert.equal(result[2].before.content,'Old explanation');assert.equal(result[2].after,null);
});
test('regeneration reveals cleared saved lessons and unchanged resubmissions stay visible',()=>{
 const reset=reviewEntries(course,{mode:'regenerate',outline,lessons:[]});
 assert.ok(reset[0].labels.includes('Content cleared'));assert.equal(reset[0].after,null);
 const rewritten=reviewEntries(course,{mode:'revise',lessons:[{lesson_key:'a',content:'Old explanation'}]});
 assert.ok(rewritten[0].labels.includes('Revised'));assert.equal(rewritten[1].changed,false);
});
test('review covers omitted practice/teaching, source changes, and structured visuals',()=>{
 const old={content:'same',teaching:{outcome:'Understand'},practice:{prompt:'Question'},visual:{kind:'sequence'},source_ids:['s1']};
 const sections=lessonSections(old,{content:'same',source_ids:['s2']},[{id:'s1',title:'Old source'},{id:'s2',title:'New source'}]);
 assert.deepEqual(sections.filter(s=>s.before!==s.after).map(s=>s.label),['Learning goals','Practice','Diagram','References']);
 assert.match(sections.at(-1).before,/Old source/);assert.match(sections.at(-1).after,/New source/);
});
