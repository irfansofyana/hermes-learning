// Conversational editing against an explicitly simulated tutor and disposable store.
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const output=resolve(process.env.LEARNING_SCREENSHOT_DIR||'/tmp/hermes-learning-updates-check');await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{}),args:process.env.LEARNING_BROWSER_NO_SANDBOX==='1'?['--no-sandbox']:[]});
const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];page.on('pageerror',error=>errors.push(error.message));page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
const api=(action,params={})=>page.evaluate(async({action,params})=>{const response=await fetch('/api/plugins/hermes-learning/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_version:1,action,params})});const value=await response.json();if(!response.ok)throw Error(JSON.stringify(value));return value;},{action,params});
const title='Conversational updates QA '+Date.now();let track;
const read=()=>api('course_read',{track_id:track.id});
async function waitIdle(){await page.getByRole('button',{name:'Send message',exact:true}).waitFor();await page.waitForFunction(()=>!document.querySelector('.lw-tutor .lw-live-dot'));await page.getByRole('button',{name:'Update this path',exact:true}).waitFor();}
async function ask(message){await page.getByLabel('Message your tutor').fill(message);await page.getByRole('button',{name:'Send message',exact:true}).click();await page.getByRole('button',{name:/^Pending changes \(/}).waitFor();await waitIdle();}
async function review(){await page.getByRole('button',{name:/^Pending changes \(/}).click();await page.getByRole('button',{name:'Review changes',exact:true}).first().click();await page.getByRole('dialog',{name:'Review learning changes'}).waitFor();}
async function apply(){await page.getByRole('button',{name:'Apply changes',exact:true}).click();await page.getByRole('dialog',{name:'Review learning changes'}).waitFor({state:'detached'});}
async function request(kind,instructions){await page.getByRole('button',{name:'Update this path',exact:true}).click();await page.getByLabel('What would you like to update?').selectOption(kind);await page.getByLabel('Tell your tutor what should change').fill(instructions);await page.getByRole('button',{name:'Ask tutor to propose changes',exact:true}).click();await page.getByRole('dialog',{name:'Update your learning path'}).waitFor({state:'detached'});await page.getByRole('button',{name:/^Pending changes \(/}).waitFor();await waitIdle();}
try{
 await page.goto(process.env.LEARNING_PREVIEW_URL||'http://127.0.0.1:8897');await page.getByText('Simulated tutor preview',{exact:true}).waitFor();
 await page.getByLabel('What do you want to learn or build?').fill(title);await page.getByRole('button',{name:'Generate learning path',exact:true}).click();await page.getByRole('heading',{name:'Understand the moving parts',exact:true}).waitFor();await waitIdle();
 const state=await page.evaluate(async()=>fetch('/api/plugins/hermes-learning/state').then(response=>response.json()));track=state.tracks.find(item=>item.title===title);assert.ok(track);
 await page.getByRole('button',{name:'Mark as read',exact:true}).click();await page.getByRole('button',{name:'Mark as unread',exact:true}).waitFor();const original=await read();
 await ask('Rewrite this lesson with a practical queue example.');await ask('Rewrite this lesson with a practical queue example.');const proposed=await read();assert.equal(proposed.revision,original.revision);assert.deepEqual(proposed.lessons,original.lessons);assert.deepEqual(proposed.position,original.position);
 // Pending revisions occupy no tutor space and can be minimized without dismissal.
 assert.equal(await page.locator('.lw-tutor .lw-proposals,.lw-tutor .lw-proposal-list').count(),0);
 assert.equal(await page.getByRole('dialog').count(),0,'Suggestions do not interrupt chat');
 const trigger=page.getByRole('button',{name:/^Pending changes \(/});
 assert.equal(await trigger.getAttribute('aria-label'),'Pending changes (2)');
 await trigger.click();const inbox=page.getByRole('dialog',{name:'Pending changes',exact:true});await inbox.waitFor();
 const summary=inbox.locator('.lw-proposal-list p').first(),originalSummary=await summary.textContent();
 await summary.evaluate(el=>{el.textContent='A long revision explanation with details about each proposed lesson change. '.repeat(80);});
 assert.ok(await summary.evaluate(el=>el.clientHeight<=parseFloat(getComputedStyle(el).lineHeight)*3+1),'Long summaries stay compact');
 await summary.evaluate((el,text)=>{el.textContent=text;},originalSummary);
 await page.screenshot({path:resolve(output,'pending-changes-desktop.png')});
 await inbox.getByRole('button',{name:'Minimize changes',exact:true}).click();await inbox.waitFor({state:'detached'});
 assert.equal(await trigger.evaluate(el=>document.activeElement===el),true,'Minimizing restores trigger focus');
 assert.deepEqual((await read()).proposals,proposed.proposals,'Minimize must not dismiss suggestions');
 await page.getByLabel('Message your tutor').fill('Keep this draft while I review.');
 await page.getByRole('button',{name:'Hide tutor',exact:true}).click();
 await trigger.click();await inbox.waitFor();await page.keyboard.press('Escape');await inbox.waitFor({state:'detached'});
 await page.getByRole('button',{name:'Open tutor',exact:true}).click();
 assert.equal(await page.getByLabel('Message your tutor').inputValue(),'Keep this draft while I review.');
 await page.getByLabel('Message your tutor').fill('');
 await page.screenshot({path:resolve(output,'minimized-changes-desktop.png')});
 await page.setViewportSize({width:390,height:844});await page.emulateMedia({colorScheme:'dark'});
 await trigger.click();await inbox.waitFor();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await page.screenshot({path:resolve(output,'pending-changes-mobile.png')});
 await inbox.getByRole('button',{name:'Minimize',exact:true}).click();await inbox.waitFor({state:'detached'});
 await page.setViewportSize({width:1440,height:1000});await page.emulateMedia({colorScheme:'light'});
 await review();await page.getByRole('button',{name:'Back to suggestions',exact:true}).click();await inbox.waitFor();await inbox.getByRole('button',{name:'Review changes',exact:true}).first().click();const dialog=page.getByRole('dialog',{name:'Review learning changes'});assert.ok(await dialog.locator('.lw-diff-added').count()>0);await dialog.getByRole('button',{name:'Preview',exact:true}).click();assert.ok(await dialog.locator('.hljs-string,.hljs-keyword,.hljs-built_in').count()>0);await dialog.getByRole('region',{name:'Current lesson preview'}).getByRole('heading',{name:'Follow the flow',exact:true}).waitFor();await dialog.getByRole('button',{name:'Changes',exact:true}).click();await page.screenshot({path:resolve(output,'lesson-change-desktop.png')});
 await page.setViewportSize({width:390,height:844});await page.emulateMedia({colorScheme:'dark'});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.equal(await dialog.evaluate(element=>element.scrollWidth>element.clientWidth),false);await page.screenshot({path:resolve(output,'lesson-change-mobile-dark.png')});await dialog.evaluate(el=>{el.scrollTop=el.scrollHeight;});const minimizeBox=await dialog.getByRole('button',{name:'Minimize changes',exact:true}).boundingBox();assert.ok(minimizeBox.y>=12&&minimizeBox.y<100,'Minimize stays visible in long previews');await dialog.evaluate(el=>{el.scrollTop=0;});await page.setViewportSize({width:1440,height:1000});await page.emulateMedia({colorScheme:'light'});
 await apply();await page.locator('.lw-reading').getByRole('heading',{name:'Practical queue walkthrough'}).waitFor();const revised=await read();assert.equal(revised.revision,original.revision+1);assert.deepEqual(revised.position.completed,[]);assert.equal(revised.lessons[0].version,original.lessons[0].version+1);
 await page.getByRole('button',{name:'Mark as read',exact:true}).click();await page.getByRole('button',{name:'Mark as unread',exact:true}).waitFor();
 await request('extend','Add a retry-safe worker project.');await page.reload();await page.locator('.lw-path').filter({hasText:title}).click();await page.getByRole('button',{name:/^Pending changes \(/}).waitFor();await waitIdle();await review();await page.getByText('Build a retry-safe worker',{exact:true}).first().waitFor();await apply();const extended=await read();assert.equal(extended.outline.length,original.outline.length+1);assert.deepEqual(extended.lessons.find(lesson=>lesson.key===revised.lessons[0].key),revised.lessons[0]);assert.deepEqual(extended.position.completed,[revised.lessons[0].key]);assert.deepEqual(extended.binding,original.binding);
 await request('regenerate','Start again with a practical beginner project.');await review();await page.getByRole('button',{name:'Dismiss suggestion',exact:true}).click();await page.getByRole('dialog',{name:'Review learning changes'}).waitFor({state:'detached'});assert.equal((await read()).revision,extended.revision);
 await ask('Regenerate the roadmap as a practical beginner course.');await review();await apply();await page.getByRole('heading',{name:'Rebuild from a concrete example',exact:true}).waitFor();const regenerated=await read();assert.equal(regenerated.revision,extended.revision+1);assert.equal(regenerated.lessons.length,1);assert.equal(regenerated.outline.length,2);assert.deepEqual(regenerated.position.completed,[]);assert.equal(regenerated.position.lesson_key,regenerated.outline[0].key);assert.deepEqual(regenerated.sources,original.sources);assert.deepEqual(regenerated.binding,original.binding);
 await page.reload();await page.locator('.lw-path').filter({hasText:title}).click();await page.getByRole('heading',{name:'Rebuild from a concrete example',exact:true}).waitFor();await page.getByRole('button',{name:'Next lesson',exact:true}).click();await page.getByRole('heading',{name:'Practice with failures',exact:true}).waitFor();await waitIdle();await page.screenshot({path:resolve(output,'regenerated-path.png')});assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'passed',proposalPreview:true,multipleSuggestions:true,minimizeWithoutDismiss:true,reviewWithoutTutor:true,draftPreserved:true,noChangeBeforeApply:true,revise:true,extend:true,regenerate:true,dismiss:true,pendingReload:true,readProgress:true,conversationPreserved:true,nextLesson:true,errors,screenshots:output}));
}catch(error){await page.screenshot({path:resolve(output,'failure.png')});console.error(await page.locator('body').innerText());throw error;}finally{await browser.close();}
