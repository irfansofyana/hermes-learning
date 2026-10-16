// Run only against the labelled local preview and a fresh, disposable store.
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const url=process.env.LEARNING_PREVIEW_URL||'http://127.0.0.1:8882';
const output=resolve(process.env.LEARNING_SCREENSHOT_DIR||'/tmp/hermes-learning-rendering-check');
await mkdir(output,{recursive:true});
const browser=await chromium.launch({...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{}),headless:true,args:process.env.LEARNING_BROWSER_NO_SANDBOX==='1'?['--no-sandbox']:[]});
const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),errors=[];
page.on('pageerror',error=>errors.push(error.message));
const code='total = 0\nfor item in [2, 4]:\n    total += item\nprint(total)';
const content='# Read and trace\n\nA disposable rendering fixture.\n\n```python\n'+code+'\n```\n\n| Input | Result |\n|---|---|\n| `2` | 2 |\n| `4` | 6 |\n\n1. Read the code.\n   - Trace the values.\n2. Explain the result.\n\n- [x] Read\n- [ ] Practise\n\nA source note[^one].\n\n[^one]: This note tests return navigation.\n';
const visuals=[
 {type:'sequence',title:'Trace the messages',participants:[{id:'a',label:'Producer'},{id:'b',label:'Broker'},{id:'c',label:'Consumer'}],steps:[{from:'a',to:'b',label:'Publish',explanation:'Append an event.'},{from:'b',to:'c',label:'Read',explanation:'Read the retained event.'},{from:'c',to:'b',label:'Commit',explanation:'Save the next position.'}]},
 {type:'state-machine',title:'Trace the lifecycle',initial:'ready',states:[{id:'ready',label:'Ready'},{id:'running',label:'Running'},{id:'done',label:'Done'}],steps:[{from:'ready',to:'running',label:'Start',explanation:'Take work.'},{from:'running',to:'ready',label:'Retry',explanation:'Return failed work.'},{from:'ready',to:'running',label:'Restart',explanation:'Try again.'},{from:'running',to:'done',label:'Complete',explanation:'Finish the job.'}]},
 {type:'code-trace',title:'Trace the code',language:'python',code,steps:[{line:1,label:'Initialize',explanation:'Start from zero.',variables:[{name:'total',value:'0'}]},{line:3,label:'First item',explanation:'Add two.',variables:[{name:'total',value:'2'}]},{line:3,label:'Second item',explanation:'Add four.',variables:[{name:'total',value:'6'}]},{line:4,label:'Result',explanation:'The illustrative result is six; this code was not run.',variables:[{name:'total',value:'6'}]}]}
];
try{
 await page.goto(url);assert.equal(await page.title(),'Hermes Learning');await page.getByText('Simulated tutor preview',{exact:true}).waitFor();
 await page.evaluate(async({visuals,content})=>{
  const base='/api/plugins/hermes-learning';
  const request=async(path,body)=>{const response=await fetch(base+path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});if(!response.ok)throw Error(await response.text());return response.json();};
  const state=await request('/state');if(state.tracks.length)throw Error('Use a fresh empty preview store; refusing to add fixtures to existing learning data.');
  const action=(name,params)=>request('/action',{api_version:1,action:name,params});
  for(const visual of visuals){
   const started=await action('course_start',{request_id:'rendering-check-'+visual.type,title:'Rendering check: '+visual.type,intent:'project',level:'beginner',materials:[]});
   const scope={context_id:started.context_id,job_id:started.job_id};
   await action('course_plan',{...scope,summary:'A disposable rendering fixture.',assumptions:['No model invocation.'],lessons:[{key:'first',title:visual.title,goal:'Explore rich text, code, and visual steps.'}]});
   await action('course_lesson',{...scope,lesson_key:'first',content,source_ids:[],visual});
  }
 },{visuals,content});
 await page.reload();await context.grantPermissions(['clipboard-read','clipboard-write'],{origin:new URL(url).origin});
 for(const {type,steps} of visuals){
  await page.locator('.lw-path').filter({hasText:'Rendering check: '+type}).click();const reading=page.locator('.lw-reading'),visual=reading.locator('.hl-sequence');await visual.waitFor();
  assert((await reading.locator('.hljs-keyword').count())>0);assert.equal(await reading.locator('table tbody tr').count(),2);assert.equal(await reading.locator('.task-list-item input:disabled').count(),2);
  const block=reading.locator('.lw-code-block').first();await block.getByRole('button',{name:'Copy code'}).click();await block.getByRole('status').getByText('Copied',{exact:true}).waitFor();assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),code);
  const footnote=reading.locator('sup a').first();const href=await footnote.getAttribute('href');await footnote.click();assert.equal(await page.evaluate(()=>location.hash),href);assert(await page.locator(href).count());const back=reading.locator('a[href*="-fnref-"]').first(),target=await back.getAttribute('href');await back.click();assert.equal(await page.evaluate(()=>location.hash),target);
  await visual.getByRole('button',{name:/Next step/}).click();await visual.getByText(`Step 2 of ${steps.length}`,{exact:true}).waitFor();const stage=visual.locator(type==='sequence'?'.hl-diagram':'.hl-visual-stage');await stage.focus();await page.keyboard.press('ArrowRight');await visual.getByText(`Step 3 of ${steps.length}`,{exact:true}).waitFor();
  if(type==='code-trace'){assert.equal(await visual.locator('[aria-current="step"]').count(),1);assert((await visual.locator('.hl-variables').innerText()).includes('6'));}
  await visual.scrollIntoViewIfNeeded();await page.screenshot({path:resolve(output,type+'-desktop.png')});await page.setViewportSize({width:390,height:844});await page.emulateMedia({colorScheme:'dark'});await page.getByRole('button',{name:'Lesson',exact:true}).click();await visual.scrollIntoViewIfNeeded();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:resolve(output,type+'-mobile.png')});
  await page.setViewportSize({width:1440,height:1000});await page.emulateMedia({colorScheme:'light'});await page.locator('.lw-brand').click();
 }
 assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'passed',visuals:visuals.map(visual=>visual.type),codeCopy:true,footnoteReturn:true,keyboardSteps:true,desktop:'1440x1000 light',mobile:'390x844 dark',errors,screenshots:output}));
}catch(error){await page.screenshot({path:resolve(output,'failure.png')});throw error;}finally{await browser.close();}
