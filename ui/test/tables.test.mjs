import test from 'node:test';
import assert from 'node:assert/strict';
import {loadRenderedModule} from './render-module.mjs';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
const {Markdown}=await loadRenderedModule('../src/CourseContent.jsx');
const render=content=>renderToStaticMarkup(React.createElement(Markdown,{content}));
const kafkaTable=`| Send step | Record key | Event | Partition | Assigned offset |
|---|---|---|---|---|
| First | order-A | OrderPlaced | 0 | 0 |
| Second | order-B | OrderPlaced | 1 | 0 |
| Third | order-A | PaymentReceived | 0 | 1 |
| Fourth | order-B | OrderCancelled | 1 | 1 |`;
test('Kafka worked trace renders as a semantic table with five columns and four data rows',()=>{
 const html=render('Imagine these events:\n\n'+kafkaTable+'\n\nThe offsets are per partition.');
 assert.ok(html.includes('<table>'));assert.equal((html.match(/<th /g)||[]).length,5);
 assert.equal((html.match(/<tr>/g)||[]).length,5);assert.equal((html.match(/<td[ >]/g)||[]).length,20);
 assert.ok(html.includes('scope="col">Assigned offset</th>'));assert.ok(html.includes('<td>PaymentReceived</td>'));
 assert.ok(html.includes('<p>The offsets are per partition.</p>'));assert.ok(!html.includes('|---|'));
 assert.ok(html.includes('tabindex="0"'),'Wide tables must have a keyboard-focusable scrolling region');
});
test('tables without outer pipes preserve alignment and inline Markdown',()=>{
 const html=render('Name | Position | Link\n:--- | :---: | ---:\n**Queue** | `0` | [Docs](https://example.org)');
 assert.match(html,/<th[^>]*text-align:left[^>]*>Name<\/th>/);assert.match(html,/<th[^>]*text-align:center[^>]*>Position<\/th>/);assert.match(html,/<th[^>]*text-align:right[^>]*>Link<\/th>/);
 assert.ok(html.includes('<strong>Queue</strong>'));assert.ok(html.includes('<code>0</code>'));assert.ok(html.includes('href="https://example.org/"'));
});
test('escaped pipes stay in cells and ragged rows match the header column count',()=>{
 const html=render('| A | B |\n|---|---|\n| left \\| right | `a\\|b` |\n| short |\n| one | two | ignored |');
 assert.ok(html.includes('<td>left | right</td>'));assert.ok(html.includes('<code>a|b</code>'));
 assert.equal((html.match(/<td[ >]/g)||[]).length,6);assert.ok(!html.includes('ignored'));
});
test('a table directly after prose starts a new block and unsafe cell content remains inert',()=>{
 const html=render('Read this trace:\n| Input | Result |\n|---|---|\n| <script>bad()</script> | [bad](javascript:alert) |');
 assert.ok(html.startsWith('<div class="lw-markdown"><p>Read this trace:</p>'));assert.ok(html.includes('<table>'));
 assert.ok(html.includes('&lt;script&gt;'));assert.ok(!html.includes('<script>'));assert.ok(!html.includes('href="javascript:'));
});
test('ordinary pipe text and fenced table examples remain text rather than tables',()=>{
 const html=render('A | B\nnot a delimiter\n\n```markdown\n'+kafkaTable+'\n```');
 assert.ok(!html.includes('<table>'));assert.ok(html.includes('A | B'));assert.ok(html.includes('|---|---|'));
 assert.ok(!render('A | B\n--- | --- | ---').includes('<table>'));
});
test('a heading or code fence after a table is not swallowed as another data row',()=>{
 const html=render('| A | B |\n|---|---|\n| one | two |\n## Next | section\n\n| C | D |\n|---|---|\n| three | four |\n```text|example\nliteral | code\n```');
 assert.equal((html.match(/<table>/g)||[]).length,2);assert.equal((html.match(/<td[ >]/g)||[]).length,4);
 assert.ok(html.includes('<h3>Next | section</h3>'));assert.match(html,/<pre\b[^>]*>[\s\S]*literal \| code[\s\S]*<\/pre>/);
});
