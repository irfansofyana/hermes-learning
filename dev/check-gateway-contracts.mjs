// Validate actual Learning request payloads against Hermes's wire schemas.
// No gateway connection, model request, profile configuration, or service restart.
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {resolve} from 'node:path';
import {branchSessionModel,modelCreateParams} from '../ui/src/model-options.mjs';
const source=process.argv[2];
if(!source)throw Error('Pass the path to a Hermes Agent checkout.');
const calls=[];
const transport={async request(method,params){
 calls.push({method,params});
 if(method==='session.activate')return {running:false};
 if(method==='model.options')return {provider:'openai',model:'fixture-default',providers:[]};
 if(method==='session.history')return {messages:[{role:'user',text:'Explain queues.'},{role:'assistant',text:'A queue returns the oldest item first.'}]};
 return {session_id:'new-runtime',stored_session_id:'new-stored'};
}};
await branchSessionModel(transport,'work','runtime','stored',{provider:'openai',model:'fixture-picked'},{idempotencyKey:'explicit-choice'});
await branchSessionModel(transport,'work','runtime','stored',null,{idempotencyKey:'default-choice'});
calls.push({method:'session.create',params:{profile:'work',title:'Practice fixture',...modelCreateParams({provider:'openai',model:'fixture-picked'}),close_on_disconnect:false,idempotency_key:'practice-fixture'}});
const result=spawnSync(process.env.HERMES_PYTHON||resolve(source,'.venv/bin/python'),['-B','-c',`
import json,sys
sys.path.insert(0,sys.argv[1])
from tui_gateway.contracts import METHODS
from pydantic import ValidationError
try:
    METHODS['session.branch_stored'].params.model_validate({'parent_session_id':'stored','provider':'openai','model':'fixture-picked','close_on_disconnect':False})
except ValidationError as error:
    fields={entry['loc'][0] for entry in error.errors() if entry['type']=='extra_forbidden'}
    assert {'provider','model','close_on_disconnect'} <= fields, fields
    print('Reproduced original invalid branch parameters: provider, model, close_on_disconnect')
else:
    print('This host also accepts branch overrides; Learning uses the compatible create contract')
for call in json.load(sys.stdin):
    METHODS[call['method']].params.model_validate(call['params'])
print('Validated all model selection and practice creation request shapes against Hermes contracts')
`,resolve(source)],{input:JSON.stringify(calls),encoding:'utf8',timeout:120000});
if(result.error)throw result.error;
assert.equal(result.status,0,result.stderr||result.stdout);
console.log(result.stdout.trim());
