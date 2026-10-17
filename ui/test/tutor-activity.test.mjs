import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {loadRenderedModule} from './render-module.mjs';
import {historyReasoning,planSnapshot,toolActivity} from '../src/tutor-activity.mjs';
const {TutorActivity,TutorPlan}=await loadRenderedModule('../src/TutorPanel.jsx');
test('thinking and activity are expandable inert text, not executable markup',()=>{
 const html=renderToStaticMarkup(React.createElement(TutorActivity,{message:{kind:'reasoning',text:'<script>alert(1)</script>\n```html\nunsafe\n```',status:'complete'}}));
 assert.match(html,/<details/);assert.doesNotMatch(html,/<script|<details[^>]* open/);assert.match(html,/&lt;script&gt;/);
 const tool=toolActivity({name:'web_search',tool_id:'a',result:{error:'no'},args:{password:'secret'}},'complete');
 const output=renderToStaticMarkup(React.createElement(TutorActivity,{message:tool}));
 assert.match(output,/Failed/);assert.doesNotMatch(output,/secret/);
});
test('plan lists actual progress and omitted plans do not fabricate steps',()=>{
 assert.equal(renderToStaticMarkup(React.createElement(TutorPlan,{plan:null})), '');
 const plan=planSnapshot({revision:1,todos:[{id:'a',content:'Read docs',status:'completed'},{id:'b',content:'Write example',status:'in_progress'}]},null);
 const html=renderToStaticMarkup(React.createElement(TutorPlan,{plan}));assert.match(html,/1\/2/);assert.match(html,/Write example/);assert.match(html,/in progress/);
});
test('provider summaries use only text and ignore encrypted reasoning',()=>{
 assert.equal(historyReasoning({codex_reasoning_items:[{encrypted_content:'opaque',summary:[{text:'Check the premise.'}]}]}),'Check the premise.');
 assert.equal(historyReasoning({reasoning_details:[{data:'encrypted'}]}),'');
});
