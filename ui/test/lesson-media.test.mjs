import test from 'node:test';
import assert from 'node:assert/strict';
import {checkedMermaid,assetId} from '../src/lesson-media.mjs';
test('diagram source rejects configuration, remote resources, and oversized definitions',()=>{
 assert.equal(checkedMermaid('flowchart LR\n A --> B'),'flowchart LR\n A --> B');
 for(const source of ['', 'x'.repeat(30001),'%%{init: {securityLevel:"loose"}}%%\ngraph TD\n A-->B','---\nconfig: {}\n---\ngraph TD\n A-->B','flowchart LR\n A@{img:"https://example.com/pixel"}','graph LR\nstyle A fill:url(//example.com/x)','graph LR;classDef bad fill:u\\72l(//example.com/x)','flowchart LR\n A@{img:"//example.com/pixel"}'])assert.throws(()=>checkedMermaid(source));
});
test('only scoped asset identities are accepted as inline image references',()=>{
 assert.equal(assetId('learning-asset:2da9-123'),'2da9-123');
 for(const url of ['file:///tmp/image.png','data:image/svg+xml,<svg/>','https://example.com/a.png','learning-asset:../secret','learning-asset:id?track=other'])assert.equal(assetId(url),null);
});
