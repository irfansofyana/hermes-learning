import test from 'node:test';
import assert from 'node:assert/strict';
import {loadRenderedModule} from './render-module.mjs';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
const {Markdown}=await loadRenderedModule('../src/CourseContent.jsx');
const render=content=>renderToStaticMarkup(React.createElement(Markdown,{content}));
test('saved opaque citations show a missing-link label instead of raw provider tokens',()=>{
 const html=render('Kafka retains events. \uE200cite\uE202turn1view0\uE202turn0search2\uE201');
 assert.ok(html.includes('Kafka retains events.'));
 assert.ok(html.includes('Source link unavailable'));
 assert.ok(!html.includes('turn1view0'));assert.ok(!html.includes('\uE200'));
 assert.ok(!html.includes('<a '),'Unknown citation handles must never be guessed into URLs');
});
test('Markdown source links remain clickable while unknown citations are explicit',()=>{
 const html=render('Reference: [Apache Kafka introduction](https://kafka.apache.org/intro/). \uE200cite\uE202turn0search3\uE201');
 assert.ok(html.includes('href="https://kafka.apache.org/intro/"'));assert.ok(html.includes('Apache Kafka introduction</a>'));
 assert.ok(html.includes('Source link unavailable'));
});
test('citation-like text in code remains literal',()=>{
 const html=render('```text\n\uE200cite\uE202turn1view0\uE201\n```\n\n`\uE200cite\uE202turn1view0\uE201`');
 assert.equal((html.match(/turn1view0/g)||[]).length,2);assert.ok(!html.includes('Source link unavailable'));
});
