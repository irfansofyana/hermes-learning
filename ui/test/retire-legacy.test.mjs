import test from 'node:test';
import assert from 'node:assert/strict';
import {clearLegacyStorage} from '../src/retire-legacy.mjs';
const storage=entries=>{const data=new Map(entries);return {get length(){return data.size;},key:index=>[...data.keys()][index],removeItem:key=>data.delete(key),data};};
test('discard old practice drafts and handoff state without removing other app or current tutor data',()=>{
 const old=['hermes-learning:draft:v1:store:track:activity','hermes-learning:draft:v1:second','hermes-learning:context','hermes-learning:tutor-request','hermes-learning:location:store'];
 const keep=['hermes-learning:tutor:v2:session','hermes-learning:unrelated','other-app:draft'];
 const saved=storage([...old,...keep].map(key=>[key,'saved']));
 clearLegacyStorage(saved);
 assert.deepEqual([...saved.data.keys()],keep);
 clearLegacyStorage(saved);
 assert.deepEqual([...saved.data.keys()],keep);
});
test('unavailable or restricted browser storage does not prevent opening Learning',()=>{
 assert.doesNotThrow(()=>clearLegacyStorage(null));
 assert.doesNotThrow(()=>clearLegacyStorage({get length(){throw new Error('Denied');}}));
});
