import {readSourceFile,SOURCE_MAX_CHARS} from './learning.mjs';
export const COURSE_MAX_CHARS=100000;
export const COURSE_MAX_BYTES=200000;
export const COURSE_MAX_SOURCES=20;
const bytes=value=>new TextEncoder().encode(value).length;
export async function readCourseFiles(files){
 return Promise.all(Array.from(files).map(async file=>{
  try{return {title:file.name,material:{...await readSourceFile(file),sharing:'selected-excerpts',read_status:'provided'}};}
  catch(error){return {title:file.name,error:error.message||'This file could not be read.'};}
 }));
}
export function linkMaterial(value){
 let url;try{url=new URL(value.trim());}catch{throw new Error('Enter a complete HTTP or HTTPS link.');}
 if(!['http:','https:'].includes(url.protocol))throw new Error('Source links must use HTTP or HTTPS.');
 if(url.href.length>2000)throw new Error('This link is too long. Use a source URL under 2,000 characters.');
 if(url.username||url.password)throw new Error('Remove credentials from the source link.');
 return {title:(url.hostname+url.pathname).slice(0,300),url:url.href,locator:url.href,excerpt:'',kind:'website',sharing:'selected-excerpts',read_status:'unread'};
}
export function pastedMaterial(value,title='Pasted notes'){
 if(!value.trim())throw new Error('Paste some text before adding it.');
 if(value.length>SOURCE_MAX_CHARS)throw new Error('Pasted material exceeds 50,000 characters. Add a smaller excerpt.');
 if(bytes(value)>200*1024)throw new Error('Pasted material exceeds 200 KB. Add a smaller excerpt.');
 if(value.includes('\0'))throw new Error('Pasted material contains binary data. Choose plain text.');
 return {title:title.trim()||'Pasted notes',locator:'Pasted material',excerpt:value,kind:'notes',sharing:'selected-excerpts',read_status:'provided'};
}
export function prepareCourse({prompt='',level='beginner',items=[]}){
 const text=prompt.trim(),materials=items.filter(item=>item.material).map(({material})=>{const {read_status,retrieval_error,...source}=material;return source;});
 if(!text&&!materials.some(source=>source.excerpt?.trim()||source.url))throw new Error('Enter a topic or add readable material or a source link to begin.');
 if(text.length>12000)throw new Error('Keep your learning request under 12,000 characters.');
 if(materials.length>COURSE_MAX_SOURCES)throw new Error('Use up to 20 sources per learning path. Remove a source to continue.');
 if(materials.reduce((sum,item)=>sum+(item.excerpt||'').length,0)>COURSE_MAX_CHARS||bytes(JSON.stringify(materials))>COURSE_MAX_BYTES)throw new Error('Your combined materials are too large. Keep the total below 100,000 characters and 200 KB by removing a source or using shorter excerpts.');
 if(!['beginner','intermediate','advanced'].includes(level))throw new Error('Choose a supported learning level.');
 return {title:Array.from(text||`Study ${materials[0].title}`).slice(0,300).join(''),interest:text||'Teach me from the supplied sources.',intent:!text?'sources':/\b(build|create|implement|develop|make|ship|project)\b/i.test(text)?'project':'topic',level,materials,prompt:text||'Teach me from the supplied sources.'};
}
