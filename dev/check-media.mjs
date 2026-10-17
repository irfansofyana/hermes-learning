// Real renderers, deterministic lesson data; never calls a model. Seed with dev/seed-media.py.
import assert from 'node:assert/strict';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.LEARNING_PREVIEW_URL||'http://127.0.0.1:8897';
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH,headless:true,args:process.env.LEARNING_BROWSER_NO_SANDBOX==='1'?['--no-sandbox']:[]});
const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[],requests=[];
page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith(base)&&!r.url().startsWith('data:'))requests.push(r.url());});
try{
 await page.goto(base);await page.getByRole('button',{name:/Kafka diagrams and saved images/}).click();
 const lesson=page.locator('.lw-reading');
 await lesson.locator('.lw-media-block').first().locator('img').waitFor();
 await lesson.locator('.lw-media-block').nth(1).locator('img').waitFor();
 await lesson.locator('.lw-saved-image img').waitFor();
 await page.waitForFunction(()=>[...document.querySelectorAll('.lw-reading .lw-media-open img')].length===3&&[...document.querySelectorAll('.lw-reading .lw-media-open img')].every(img=>img.complete&&img.naturalWidth>0));
 assert.equal(await lesson.locator('.lw-media-error').count(),2,'Malformed and forbidden diagrams fail visibly');
 assert.equal(await lesson.locator('.lw-media-source[open]').count(),2,'Invalid sources remain readable');
 await page.screenshot({path:'/tmp/learning-media-desktop.png'});
 await lesson.locator('.lw-media-open').first().click();
 const modal=page.getByRole('dialog',{name:'Mermaid diagram',exact:true});await modal.waitFor();
 await modal.getByRole('button',{name:'Zoom in',exact:true}).click();assert.equal(await modal.locator('.lw-media-pan img').evaluate(el=>el.style.width),'125%');
 await modal.getByRole('button',{name:'Fit',exact:true}).click();await page.keyboard.press('Escape');await modal.waitFor({state:'detached'});
 await lesson.locator('.lw-media-source').first().getByText('Diagram source',{exact:true}).click();await lesson.locator('.lw-media-source').first().getByRole('button',{name:'Copy code',exact:true}).waitFor();
 await page.getByRole('button',{name:/Pending changes/}).click();await page.getByRole('button',{name:'Review changes',exact:true}).click();
 const review=page.getByRole('dialog',{name:'Review learning changes'});await review.waitFor();await review.getByRole('button',{name:'Preview',exact:true}).click();
 await page.waitForFunction(()=>[...document.querySelectorAll('[aria-label="Proposed lesson preview"] .lw-media-open img')].filter(img=>img.checkVisibility()).length===3&&[...document.querySelectorAll('[aria-label="Proposed lesson preview"] .lw-media-open img')].filter(img=>img.checkVisibility()).every(img=>img.complete&&img.naturalWidth>0));
 // An enlarged diagram is a second native modal; closing it keeps the review open.
 await review.locator('.lw-media-open:visible').first().click();await modal.waitFor();await page.keyboard.press('Escape');await modal.waitFor({state:'detached'});await review.waitFor();
 await page.getByRole('button',{name:'Close preview',exact:true}).click();
 await page.reload();await page.getByRole('button',{name:/Kafka diagrams and saved images/}).click();
 await page.waitForFunction(()=>[...document.querySelectorAll('.lw-reading .lw-media-open img')].length===3&&[...document.querySelectorAll('.lw-reading .lw-media-open img')].every(img=>img.complete&&img.naturalWidth>0));
 await page.setViewportSize({width:390,height:844});await page.emulateMedia({colorScheme:'dark'});
 await lesson.locator('.lw-media-block').first().scrollIntoViewIfNeeded();await page.screenshot({path:'/tmp/learning-media-mobile.png'});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[],'No CDN, tracking pixels, or external resources');
 console.log(JSON.stringify({passed:true,mermaid:true,archify:true,savedPNGAfterOriginalDeleted:true,invalidSourceFallback:true,proposalPreview:true,nestedEnlarge:true,zoom:true,reload:true,mobile:true,noExternalRequests:true,errors}));
}catch(e){await page.screenshot({path:'/tmp/learning-media-failure.png'});console.error(await page.locator('body').innerText());throw e;}finally{await browser.close();}
