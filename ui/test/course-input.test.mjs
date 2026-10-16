import test from 'node:test';
import assert from 'node:assert/strict';
import {readCourseFiles,linkMaterial,pastedMaterial,prepareCourse,COURSE_MAX_CHARS} from '../src/course-input.mjs';
const file=(name,content)=>({name,size:new TextEncoder().encode(content).length,arrayBuffer:async()=>new TextEncoder().encode(content).buffer});
test('multiple imports preserve readable files and report every unsupported file',async()=>{
 const items=await readCourseFiles([file('notes.md','# Notes'),file('report.pdf','binary'),file('queue.go','package main')]);
 assert.equal(items.length,3);assert.equal(items[0].material.excerpt,'# Notes');assert.match(items[1].error,/PDF/);assert.equal(items[2].material.kind,'repository');
});
test('source links allow only HTTP(S) and remain explicitly unread',()=>{
 assert.throws(()=>linkMaterial('javascript:alert(1)'),/HTTP/);assert.throws(()=>linkMaterial('file:///etc/passwd'),/HTTP/);
 const source=linkMaterial('https://example.org/repository');assert.equal(source.read_status,'unread');assert.equal(source.excerpt,'');
});
test('a topic can proceed with failed files while a source-only empty request cannot',()=>{
 const broken={title:'report.pdf',error:'Unsupported PDF'};
 assert.throws(()=>prepareCourse({prompt:'',items:[broken]}),/topic|readable/i);
 assert.equal(prepareCourse({prompt:'Learn queue design',items:[broken]}).materials.length,0);
 const fromSources=prepareCourse({prompt:'',items:[{material:pastedMaterial('Useful notes')}]});
 assert.equal(fromSources.intent,'sources');assert.ok(fromSources.interest.trim());assert.equal('read_status' in fromSources.materials[0],false);
});
test('pasted text and aggregate source limits reject oversized input without truncation',()=>{
 assert.throws(()=>pastedMaterial('a'.repeat(50001)),/50,000/);
 const material=pastedMaterial('a'.repeat(50000));
 assert.throws(()=>prepareCourse({prompt:'Study this',items:Array.from({length:Math.ceil(COURSE_MAX_CHARS/50000)+1},()=>({material}))}),/combined|total/i);
});
test('preparation preserves full learner request, source locators, sharing and selected level',()=>{
 const result=prepareCourse({prompt:'Build a worker pool in Go',level:'advanced',items:[{material:pastedMaterial('go notes','Concurrency notes')}]});
 assert.equal(result.intent,'project');assert.equal(result.level,'advanced');assert.equal(result.materials[0].sharing,'selected-excerpts');assert.equal(result.materials[0].locator,'Pasted material');assert.equal(result.prompt,'Build a worker pool in Go');
});
test('UTF-8 aggregate limit handles multibyte material before model work',()=>{
 const material=pastedMaterial('界'.repeat(40000));
 assert.throws(()=>prepareCourse({prompt:'Study notes',items:[{material},{material}]}),/combined/);
});
test('links with embedded credentials are rejected and long paths keep bounded titles',()=>{
 assert.throws(()=>linkMaterial('https://name:secret@example.org/notes'),/credentials/);
 assert.equal(linkMaterial('https://example.org/'+ 'a'.repeat(400)).title.length,300);
});
test('generated Markdown renders source HTML and unsafe links as inert text',async()=>{
 const {build}=await import('esbuild');
 const {renderToStaticMarkup}=await import('react-dom/server');
 const React=await import('react');
 const built=await build({entryPoints:[new URL('../src/CourseContent.jsx',import.meta.url).pathname],bundle:true,write:false,format:'esm',platform:'node',loader:{'.jsx':'jsx'}});
 const {Markdown}=await import(`data:text/javascript;base64,${Buffer.from(built.outputFiles[0].text).toString('base64')}`);
 const markup=renderToStaticMarkup(React.createElement(Markdown,{content:'# Test\n\n<script>alert(1)</script>\n\n[unsafe](javascript:alert) [safe](https://example.org)\n\n```html\n<img src=x onerror=alert(1)>\n```'}));
 assert.ok(!markup.includes('<script>'));assert.ok(!markup.includes('<img '));assert.ok(!markup.includes('href="javascript:'));assert.ok(markup.includes('href="https://example.org/"'));assert.ok(markup.includes('&lt;script&gt;'));
});
