// Hold simulated publication to exercise navigation while a tutor turn is active.
import assert from 'node:assert/strict';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH,headless:true,args:process.env.LEARNING_BROWSER_NO_SANDBOX==='1'?['--no-sandbox']:[]});
const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];page.on('pageerror',error=>errors.push(error.message));
const url=process.env.LEARNING_PREVIEW_URL||'http://127.0.0.1:8897';
let release,started,held=new Promise(resolve=>started=resolve),gate=new Promise(resolve=>release=resolve),generated=0,failThird=true;
try{
 await page.goto(url);await page.getByText('Simulated tutor preview',{exact:true}).waitFor();
 const tracks=await page.evaluate(async()=>{
  const action=async(action,params)=>{const r=await fetch('/api/plugins/hermes-learning/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_version:1,action,params})});if(!r.ok)throw Error(await r.text());return r.json();};
  const result=[];
  for(const label of ['Navigation A','Navigation B']){
   const title=label+' '+Date.now();
   const course=await action('course_start',{request_id:crypto.randomUUID(),title,intent:'topic',level:'beginner',materials:[]});
   const scope={context_id:course.context_id,job_id:course.job_id};
   await action('course_plan',{...scope,summary:label,assumptions:[],lessons:[{key:'first',title:label+' first',goal:'Read saved content'},{key:'second',title:label+' second',goal:'Generate in background'},{key:'third',title:label+' third',goal:'Preview a future lesson'}]});
   await action('course_lesson',{...scope,lesson_key:'first',content:'A saved lesson for navigation checks.',source_ids:[]});result.push({...course,title});
  }
  return result;
 });
 await page.reload();await page.locator('.lw-path').filter({hasText:tracks[0].title}).click();
 await page.route('**/api/plugins/hermes-learning/action',async route=>{
  const body=route.request().postDataJSON();if(body.action==='course_generate')generated++;
  if(body.action==='course_lesson'&&body.params.lesson_key==='third'&&failThird){failThird=false;await route.fulfill({status:500,contentType:'application/json',body:JSON.stringify({detail:'Simulated publication failure'})});return;}
  if(body.action==='course_lesson'&&body.params.lesson_key==='second'){started();await gate;}
  await route.continue();
 });
 await page.getByRole('button',{name:/02.*Navigation A second/}).click();await held;
 assert.equal(await page.getByRole('button',{name:/01.*Navigation A first/}).isEnabled(),true,'Saved lessons must remain navigable during generation');
 await page.getByRole('button',{name:/01.*Navigation A first/}).click();await page.getByRole('heading',{name:'Navigation A first',exact:true}).waitFor();
 await page.getByRole('button',{name:/03.*Navigation A third/}).click();await page.getByRole('heading',{name:'Navigation A third',exact:true}).waitFor();
 assert.equal(await page.getByRole('button',{name:'Generate lesson',exact:true}).isDisabled(),true);
 assert.equal(generated,1,'Browsing an ungenerated lesson must not start another job');
 await page.getByRole('button',{name:/01.*Navigation A first/}).click();
 await page.getByRole('button',{name:'All learning paths',exact:true}).click();await page.getByRole('heading',{name:'What do you want to learn or build?'}).waitFor();
 await page.getByRole('button',{name:'Return to active tutor',exact:true}).waitFor();
 await page.locator('.lw-path').filter({hasText:tracks[1].title}).click();await page.getByRole('heading',{name:'Navigation B first',exact:true}).waitFor();
 assert.equal(await page.locator('.lw-message').count(),0,'A different path must not display the active tutor transcript');
 await page.getByRole('button',{name:'Return to active tutor',exact:true}).click();await page.getByRole('heading',{name:'Navigation A first',exact:true}).waitFor();
 await page.getByRole('button',{name:'All learning paths',exact:true}).click();
 await page.locator('.lw-path').filter({hasText:tracks[1].title}).click();
 await page.setViewportSize({width:800,height:900});
 const returnBox=await page.getByRole('button',{name:'Return to active tutor',exact:true}).boundingBox();
 assert.ok(await page.evaluate(({x,y})=>document.elementFromPoint(x,y)?.closest('button')?.textContent.includes('Return to active tutor'),{x:returnBox.x+returnBox.width/2,y:returnBox.y+returnBox.height/2}),'Tablet tutor must not cover the return button');
 await page.setViewportSize({width:390,height:844});await page.getByRole('button',{name:'Lesson',exact:true}).click();
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 release();
 await page.waitForFunction(async track_id=>{const r=await fetch('/api/plugins/hermes-learning/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_version:1,action:'course_read',params:{track_id}})});return (await r.json()).jobs.at(-1).status==='completed';},tracks[0].track_id);
 assert.equal(await page.locator('.lw-lesson-body h1').textContent(),'Navigation B first','Background completion must not replace the path being viewed');
 await page.getByRole('button',{name:'Return to active tutor',exact:true}).click();
 await page.getByRole('heading',{name:'Navigation A first',exact:true}).waitFor();
 await page.setViewportSize({width:1440,height:1000});
 await page.waitForFunction(()=>document.querySelector('.lw-tutor-status')?.textContent==='Ready');
 assert.equal(await page.locator('.lw-lesson-body h1').textContent(),'Navigation A first','Completion must not move the reader');
 const saved=await page.evaluate(async track_id=>{const r=await fetch('/api/plugins/hermes-learning/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_version:1,action:'course_read',params:{track_id}})});return r.json();},tracks[0].track_id);
 assert.equal(saved.position.lesson_key,'first');assert.equal(saved.lessons.length,2);assert.equal(saved.jobs.at(-1).status,'completed');
 assert.equal(generated,1);
 await page.getByRole('button',{name:/03.*Navigation A third/}).click();
 await page.getByRole('button',{name:'Retry lesson generation',exact:true}).click();
 await page.locator('.lw-reading .lw-markdown').first().waitFor();
 await page.waitForFunction(()=>document.querySelector('.lw-tutor-status')?.textContent==='Ready');
 const position=await page.evaluate(async track_id=>{const r=await fetch('/api/plugins/hermes-learning/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_version:1,action:'course_read',params:{track_id}})});return (await r.json()).position.lesson_key;},tracks[0].track_id);
 assert.equal(position,'third','Retry saves the currently selected lesson position');assert.equal(generated,3);assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'passed',savedLessonNavigation:true,futureLessonPreview:true,homeAndOtherPath:true,tutorPreserved:true,completionKeepsPosition:true,backgroundCompletionIsolation:true,mobileNavigation:true,failedPublicationRetry:true,errors}));
}finally{release?.();await browser.close();}
