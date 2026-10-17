import React,{Children,memo,useId} from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {Visual} from './Visual.jsx';
import {DiagramBlock,SavedImage} from './LessonMedia.jsx';
import {assetId} from './lesson-media.mjs';
import {CodeBlock} from './CodeBlock.jsx';

export function safeCourseURL(value){
 try{const url=new URL(value);return ['https:','http:'].includes(url.protocol)&&!url.username&&!url.password?url.href:null;}catch{return null;}
}
function markdownURL(value){return value.startsWith('#')||assetId(value)?value:safeCourseURL(value);}
function citationText(){
 return tree=>{
  function visit(node){
   if(node.type==='text')node.value=node.value.replace(/\uE200cite\uE202[^\uE201\r\n]*\uE201/g,'[Source link unavailable]');
   for(const child of node.children||[])visit(child);
  }
  visit(tree);
 };
}
function scopeFootnotes({prefix}){
 return tree=>{
  function visit(node){
   if(node.properties?.id==='footnote-label')node.properties.id=prefix+'footnote-label';
   for(const key of ['ariaDescribedBy','ariaLabelledBy'])if(Array.isArray(node.properties?.[key]))node.properties[key]=node.properties[key].map(id=>id==='footnote-label'?prefix+id:id);
   for(const child of node.children||[])visit(child);
  }
  visit(tree);
 };
}
const components={
 p:({children,node})=>node?.children?.some(child=>child.tagName==='img')?<div className="lw-media-paragraph">{children}</div>:<p>{children}</p>,
 h1:({children,id})=><h2 id={id}>{children}</h2>,h2:({children,id})=><h3 id={id}>{children}</h3>,h3:({children,id})=><h4 id={id}>{children}</h4>,h4:({children,id})=><h5 id={id}>{children}</h5>,h5:({children,id})=><h6 id={id}>{children}</h6>,
 a:({href,children,...props})=>assetId(href)?<span>{children}</span>:href?<a href={href} id={props.id} aria-label={props['aria-label']} aria-describedby={props['aria-describedby']} {...(href.startsWith('#')?{}:{target:'_blank',rel:'noopener noreferrer'})}>{children}</a>:<span>{children}</span>,
 img:({src,alt})=>assetId(src)?<SavedImage src={src} alt={alt}/>:src?<a href={src} target="_blank" rel="noopener noreferrer">{alt||'Open image'}</a>:<span>{alt||'Image unavailable'}</span>,
 pre:({children})=>{const child=Children.toArray(children)[0],language=child?.props?.className?.replace(/^language-/,''),source=String(child?.props?.children||'').replace(/\n$/,'');if(['mermaid','archify'].includes(language))return <DiagramBlock language={language} source={source}/>;return <CodeBlock code={String(child?.props?.children||'').replace(/\n$/,'')} language={child?.props?.className?.replace(/^language-/,'')||''}/>;},
 table:({children})=><div className="lw-table-wrap" role="region" aria-label="Lesson table" tabIndex={0}><table>{children}</table></div>,
 th:({children,style})=><th scope="col" style={style}>{children}</th>
};
const plugins=[remarkGfm,citationText];
export const Markdown=memo(function Markdown({content=''}){
 const prefix=`learning-${useId().replace(/[^a-zA-Z0-9-]/g,'')}-`;
 return <div className="lw-markdown"><ReactMarkdown remarkPlugins={plugins} rehypePlugins={[[scopeFootnotes,{prefix}]]} remarkRehypeOptions={{clobberPrefix:prefix}} components={components} urlTransform={markdownURL}>{String(content)}</ReactMarkdown></div>;
});
export default memo(function CourseContent({lesson,sources=[]}){
 const cited=sources.filter(source=>(lesson.source_ids||[]).includes(source.id));
 // Lessons are explanations: all visual steps are available, including older saved lessons.
 const visual=lesson.visual&&{...lesson.visual,visible_steps:lesson.visual.steps.length,total_steps:lesson.visual.steps.length};
 return <><Markdown content={lesson.content}/>{visual&&<Visual visual={visual}/>} {cited.length>0&&<section className="lw-references"><h2>Lesson references</h2><p>Material cited by your tutor. Citations do not independently verify a claim.</p><ul>{cited.map(source=><li key={source.id}>{safeCourseURL(source.url)?<a href={safeCourseURL(source.url)} target="_blank" rel="noopener noreferrer">{source.title} ↗</a>:<strong>{source.title}</strong>}<span>{source.locator||'Attached material'} · {source.read_status==='unread'?'Link · not read':source.read_status==='provided'?'Text supplied':source.read_status||'Read status unknown'}</span></li>)}</ul></section>}</>;
});
