import test from 'node:test';
import assert from 'node:assert/strict';
import {loadRenderedModule} from './render-module.mjs';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
const {Markdown,default:CourseContent}=await loadRenderedModule('../src/CourseContent.jsx');
const render=content=>renderToStaticMarkup(React.createElement(Markdown,{content}));
const codeText=html=>html.match(/<code\b[^>]*>([\s\S]*?)<\/code>/)?.[1].replace(/<[^>]*>/g,'').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#x27;/g,"'").replace(/&amp;/g,'&');
const examples=[['js','const answer = 42; // value'],['typescript','const name: string = "Hermes";'],['python','def square(n):\n    return n * n'],['go','package main\nfunc main() { println(42) }'],['json','{"ok": true, "count": 42}'],['sql','SELECT id FROM events WHERE id = 42;'],['bash','echo "$HOME"'],['yaml','enabled: true\ncount: 42'],['html','<div class="example">Hello</div>']];
for(const [language,code] of examples)test(`fenced ${language} code is highlighted without changing its text`,()=>{
 const html=render('```'+language+'\n'+code+'\n```');
 assert.ok(html.includes('class="hljs-'),'Recognized code needs syntax tokens');
 assert.equal(codeText(html),code);assert.ok(html.includes('Copy code'));
});
test('unknown and missing code languages fall back to readable text',()=>{
 for(const label of ['not-a-language','']){
  const html=render('```'+label+'\nhello <world> & goodbye\n```');
  assert.equal(codeText(html),'hello <world> & goodbye');assert.ok(!html.includes('class="hljs-'));assert.ok(!html.includes('<world>'));
 }
});
test('inline code stays inline and alternate code fences retain syntax highlighting',()=>{
 const inline=render('Use `queue.pop()` here.');assert.ok(!inline.includes('<pre'));assert.ok(!inline.includes('Copy code'));assert.ok(inline.includes('<code>queue.pop()</code>'));
 const code='const limit = 3;';const html=render('~~~javascript\n'+code+'\n~~~');assert.ok(html.includes('class="hljs-keyword"'));assert.equal(codeText(html),code);
});
test('nested lists, tasks, strikethrough, and footnotes render as rich lesson content',()=>{
 const html=render('3. First step\n   - Nested explanation\n4. Next step\n\n- [x] Read\n- [ ] Try\n\n~~Old assumption~~\n\nA source note[^one].\n\n[^one]: The original note.');
 assert.ok(html.includes('<ol start="3">'));assert.match(html,/<li>First step[\s\S]*<ul>/);assert.ok(html.includes('contains-task-list'));
 assert.equal((html.match(/type="checkbox"/g)||[]).length,2);assert.ok(html.includes('disabled=""'));assert.ok(html.includes('<del>Old assumption</del>'));
 assert.match(html,/href="#learning-[^"]+-fn-one"/);assert.ok(html.includes('The original note.'));assert.match(html,/id="learning-[^"]+-fnref-one"/);assert.match(html,/id="learning-[^"]+-footnote-label"/);
});
test('rich content never executes HTML or loads remote images automatically',()=>{
 const html=render('<script>window.stolen = true</script>\n\n![Remote figure](https://example.org/track.png)\n\n[bad](javascript:alert)\n\n```html\n<img src=x onerror=alert(1)>\n```');
 assert.ok(!html.includes('<script>'));assert.ok(!html.includes('<img '));assert.ok(!html.includes('href="javascript:'));assert.ok(html.includes('&lt;script&gt;'));assert.ok(html.includes('Remote figure'));
});
const visuals=[
 {type:'sequence',participants:[{id:'producer',label:'Producer'},{id:'consumer',label:'Consumer'}],steps:[{from:'producer',to:'consumer',label:'Publish',explanation:'Send an event.'},{from:'consumer',to:'producer',label:'Acknowledge',explanation:'Second step explanation.'}]},
 {type:'state-machine',states:[{id:'ready',label:'Ready'},{id:'done',label:'Done'}],initial:'ready',steps:[{from:'ready',to:'done',label:'Complete',explanation:'Finish work.'},{from:'done',to:'ready',label:'Reset',explanation:'Second step explanation.'}]},
 {type:'code-trace',language:'python',code:'count = 1\ncount += 1',steps:[{line:1,label:'Initialize',explanation:'Start with one.',variables:[{name:'count',value:'1'}]},{line:2,label:'Increment',explanation:'Second step explanation.',variables:[{name:'count',value:'2'}]}]}
];
for(const visual of visuals)test(`a saved ${visual.type} lesson exposes all visual steps without practice gates`,()=>{
 const html=renderToStaticMarkup(React.createElement(CourseContent,{lesson:{content:'An illustrated explanation.',visual:{...visual,title:'Follow the example',visible_steps:0},source_ids:[]}}));
 assert.ok(html.includes('Step 1 of 2'));assert.ok(html.includes('Second step explanation.'));assert.ok(!html.includes('opens after you submit'));
 if(visual.type==='sequence')assert.ok(html.includes('<svg'));
 if(visual.type==='code-trace'){assert.ok(html.includes('class="hljs-number"'));assert.ok(html.includes('aria-current="step"'));}
});
test('footnote references and backlinks remain local to each lesson or chat message',()=>{
 const content='A note[^one].\n\n[^one]: Details.';
 const html=renderToStaticMarkup(React.createElement(React.Fragment,null,React.createElement(Markdown,{content}),React.createElement(Markdown,{content})));
 const ids=[...html.matchAll(/ id="([^"]+)"/g)].map(match=>match[1]);
 assert.equal(new Set(ids).size,ids.length,'Separate messages must not share footnote IDs');
 for(const match of html.matchAll(/href="#([^"]+)"/g))assert.ok(ids.includes(match[1]),'Each footnote link needs its own destination');
 for(const match of html.matchAll(/aria-describedby="([^"]+)"/g))assert.ok(ids.includes(match[1]),'Footnote descriptions need a matching heading');
});
