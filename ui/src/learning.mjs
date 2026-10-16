export const SOURCE_MAX_BYTES = 200 * 1024;
export const SOURCE_MAX_CHARS = 50000;
export const SOURCE_EXTENSIONS = ['txt','md','markdown','rst','py','js','jsx','ts','tsx','mjs','cjs','json','yaml','yml','toml','csv','sql','html','css','go','rs','java','c','h','cpp','hpp','sh','rb','swift','kt'];
export const SOURCE_ACCEPT = SOURCE_EXTENSIONS.map(ext=>`.${ext}`).join(',');

export async function readSourceFile(file) {
 if (!file || typeof file.arrayBuffer !== 'function') throw new Error('Choose a text, Markdown, or code file.');
 const extension = file.name.split('.').at(-1).toLowerCase();
 if (!SOURCE_EXTENSIONS.includes(extension)) throw new Error('Choose a supported text, Markdown, or code file. PDF and image import are not available.');
 if (file.size > SOURCE_MAX_BYTES) throw new Error('This file is larger than 200 KB. Select a smaller excerpt first.');
 const buffer = await file.arrayBuffer();
 if (buffer.byteLength > SOURCE_MAX_BYTES) throw new Error('This file is larger than 200 KB.');
 let excerpt;
 try { excerpt = new TextDecoder('utf-8', {fatal:true}).decode(buffer); }
 catch { throw new Error('This file is not valid UTF-8 text. Save a UTF-8 copy and select it again.'); }
 if (excerpt.includes('\0')) throw new Error('This file contains binary data. Choose a plain text file.');
 if (excerpt.length > SOURCE_MAX_CHARS) throw new Error('This file exceeds 50,000 characters. Select a smaller excerpt first.');
 if (!excerpt.trim()) throw new Error('This file is empty. Choose a file with text to study.');
 return {title:file.name,locator:`File: ${file.name}`,excerpt,kind:['txt','md','markdown','rst','csv'].includes(extension)?'notes':'repository'};
}

export const visibleSteps = visual => Array.isArray(visual?.steps) ? visual.steps.slice(0,Number.isInteger(visual.visible_steps)?Math.max(0,visual.visible_steps):visual.steps.length) : [];
