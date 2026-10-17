// Reproduce Desktop's app-shell selection rules in the labelled, disposable preview.
import assert from 'node:assert/strict';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const url=process.env.LEARNING_PREVIEW_URL||'http://127.0.0.1:8897';
const browser=await chromium.launch({...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{}),headless:true,args:process.env.LEARNING_BROWSER_NO_SANDBOX==='1'?['--no-sandbox']:[]});
const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),errors=[];
page.on('pageerror',error=>errors.push(error.message));
async function selectAndCopy(locator){
 await locator.scrollIntoViewIfNeeded();
 const target=await locator.evaluate(element=>{
  getSelection().removeAllRanges();
  const walker=document.createTreeWalker(element,NodeFilter.SHOW_TEXT);
  let node;while((node=walker.nextNode())&&!node.textContent.trim()){}
  if(!node)throw Error('No text to select');
  const start=node.textContent.search(/\S/),end=Math.min(start+18,node.textContent.length);
  const range=document.createRange();range.setStart(node,start);range.setEnd(node,start+1);const first=range.getBoundingClientRect();
  range.setStart(node,end-1);range.setEnd(node,end);const last=range.getBoundingClientRect();
  return {text:node.textContent.slice(start,end),x1:first.left,y1:first.top+first.height/2,x2:last.right,y2:last.top+last.height/2};
 });
 await page.mouse.move(target.x1,target.y1);await page.mouse.down();await page.mouse.move(target.x2,target.y2,{steps:12});await page.mouse.up();
 assert.equal(await page.evaluate(()=>getSelection().toString()),target.text,'Mouse drag must select visible plugin text');
 await page.keyboard.press('Control+c');
 assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),target.text,'Native Copy must receive the selected text');
}
try{
 await page.goto(url);await page.getByText('Simulated tutor preview',{exact:true}).waitFor();
 await context.grantPermissions(['clipboard-read','clipboard-write'],{origin:new URL(url).origin});
 // These host rules are intentionally absent from the standalone preview.
 await page.addStyleTag({content:'body{-webkit-user-select:none;user-select:none}button,[role="button"],svg{-webkit-user-select:none;user-select:none}input,textarea{-webkit-user-select:text;user-select:text}'});
 const title='Selection and clipboard check '+Date.now();
 await page.getByLabel('What do you want to learn or build?').fill(title);
 await page.getByLabel('Attach text, Markdown, or code files').setInputFiles({name:'notes.md',mimeType:'text/markdown',buffer:Buffer.from('Reference material that can be selected and copied.')});
 await page.getByRole('button',{name:'Generate learning path',exact:true}).click();
 await page.getByRole('heading',{name:'Understand the moving parts',exact:true}).waitFor();
 await page.getByRole('button',{name:'Mark as read',exact:true}).waitFor();
 await selectAndCopy(page.locator('.lw-lesson-body h1'));
 await selectAndCopy(page.locator('.lw-reading .lw-markdown p').first());
 await selectAndCopy(page.locator('.lw-code-block code').first());
 await selectAndCopy(page.locator('.lw-message.is-user p').first());
 await selectAndCopy(page.locator('.lw-message.is-assistant p').first());
 await page.locator('.lw-thinking summary').first().click();await selectAndCopy(page.locator('.lw-thinking-text').first());
 await page.getByRole('button',{name:/Source material/}).click();
 await page.locator('.lw-source-detail summary').first().click();await selectAndCopy(page.locator('.lw-source-detail pre').first());
 assert.equal(await page.locator('.lw-send').evaluate(element=>getComputedStyle(element).userSelect),'none');
 assert.equal(await page.getByLabel('Message your tutor').evaluate(element=>getComputedStyle(element).userSelect),'text');
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:'passed',hostSelectionRules:true,mouseSelectionAndCopy:['lesson title','lesson text','code','user message','tutor reply','thinking','source text'],errors}));
}finally{await browser.close();}
