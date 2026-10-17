// Seed with dev/seed-media.py and serve the returned disposable data directory.
import assert from 'node:assert/strict';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.LEARNING_PREVIEW_URL||'http://127.0.0.1:8898';
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH,headless:true,args:process.env.LEARNING_BROWSER_NO_SANDBOX==='1'?['--no-sandbox']:[]});
const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(base);await page.getByRole('button',{name:/Kafka diagrams and saved images/}).click();
 await page.getByRole('button',{name:/Pending changes/}).click();await page.getByRole('button',{name:'Review changes',exact:true}).click();
 const review=page.getByRole('dialog',{name:'Review learning changes'});
 assert.equal(await review.getByRole('button',{name:'Changes',exact:true}).getAttribute('aria-pressed'),'true');
 assert.ok(await review.locator('.lw-diff-added').count()>0);
 const context=review.locator('.lw-diff-context').first();await context.locator('summary').click();assert.equal(await context.getAttribute('open'),'');await context.locator('summary').click();
 await review.getByRole('button',{name:'Preview',exact:true}).click();
 const proposed=review.getByRole('region',{name:'Proposed lesson preview'});
 await proposed.locator('.lw-media-open').first().waitFor();
 await page.waitForFunction(()=>[...document.querySelectorAll('[aria-label="Proposed lesson preview"] .lw-media-open img')].length===3&&[...document.querySelectorAll('[aria-label="Proposed lesson preview"] .lw-media-open img')].every(i=>i.complete&&i.naturalWidth>0));
 await proposed.locator('.lw-media-open').first().click();
 await page.getByRole('dialog',{name:'Mermaid diagram',exact:true}).waitFor();await page.keyboard.press('Escape');await review.waitFor();
 await review.getByRole('button',{name:'Changes',exact:true}).click();
 await page.screenshot({path:'/tmp/learning-review-desktop.png'});
 await review.getByRole('button',{name:'Minimize changes'}).click();await review.waitFor({state:'detached'});
 await page.getByRole('button',{name:/Pending changes/}).click();
 if(await page.getByRole('button',{name:'Review changes',exact:true}).count())await page.getByRole('button',{name:'Review changes',exact:true}).click();
 await page.setViewportSize({width:390,height:844});await page.emulateMedia({colorScheme:'dark'});
 await page.screenshot({path:'/tmp/learning-review-mobile.png'});
 assert.equal(await review.evaluate(el=>el.scrollWidth>el.clientWidth),false,'Review fits mobile');
 await review.getByRole('button',{name:'Apply changes',exact:true}).click();await review.waitFor({state:'detached'});
 await page.reload();await page.getByRole('button',{name:/Kafka diagrams and saved images/}).click();
 await page.getByText('Each diagram can be enlarged.',{exact:true}).waitFor();
 assert.equal(await page.getByRole('button',{name:/Pending changes/}).count(),0);
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({passed:true,diff:true,contextExpansion:true,renderedMedia:true,nestedModal:true,minimize:true,mobile:true,applyAndReload:true,errors}));
}catch(e){await page.screenshot({path:'/tmp/learning-review-failure.png'});throw e;}finally{await browser.close();}
