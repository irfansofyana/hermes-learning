import React from 'react';
import {Visual} from './Visual.jsx';

export function safeCourseURL(value){
 try{const url=new URL(value);return ['https:','http:'].includes(url.protocol)?url.href:null;}catch{return null;}
}
function Inline({text}){
 // React escapes every source token. Raw HTML, images, and executable URLs are never interpreted.
 const parts=String(text).split(/(`[^`\n]+`|\*\*[^*\n]+\*\*|\*[^*\n]+\*|\[[^\]\n]+\]\([^\s)]+\))/g);
 return parts.map((part,i)=>{
  if(part.startsWith('`')&&part.endsWith('`'))return <code key={i}>{part.slice(1,-1)}</code>;
  if(part.startsWith('**')&&part.endsWith('**'))return <strong key={i}>{part.slice(2,-2)}</strong>;
  if(part.startsWith('*')&&part.endsWith('*'))return <em key={i}>{part.slice(1,-1)}</em>;
  const link=part.match(/^\[([^\]]+)\]\(([^)]+)\)$/),href=link&&safeCourseURL(link[2]);
  if(href)return <a key={i} href={href} target="_blank" rel="noopener noreferrer">{link[1]}</a>;
  return part;
 });
}
export function Markdown({content=''}){
 const lines=String(content).replace(/\r\n/g,'\n').split('\n'),blocks=[];
 for(let i=0;i<lines.length;){
  const line=lines[i];
  if(!line.trim()){i++;continue;}
  if(/^\s*```/.test(line)){const language=line.trim().slice(3),code=[];i++;while(i<lines.length&&!/^\s*```/.test(lines[i]))code.push(lines[i++]);if(i<lines.length)i++;blocks.push(<div className="lw-code-block" key={i}>{language&&<div className="lw-code-language">{language}</div>}<pre><code>{code.join('\n')}</code></pre></div>);continue;}
  const heading=line.match(/^(#{1,6})\s+(.+)$/);
  if(heading){const Tag=`h${Math.min(heading[1].length+1,6)}`;blocks.push(<Tag key={i}><Inline text={heading[2]}/></Tag>);i++;continue;}
  if(/^\s*([-*_])(?:\s*\1){2,}\s*$/.test(line)){blocks.push(<hr key={i++}/>);continue;}
  if(/^\s*>\s?/.test(line)){const quote=[];while(i<lines.length&&/^\s*>/.test(lines[i]))quote.push(lines[i++].replace(/^\s*>\s?/,''));blocks.push(<blockquote key={i}><Inline text={quote.join(' ')}/></blockquote>);continue;}
  if(/^\s*(?:[-*+]\s|\d+[.)]\s)/.test(line)){const ordered=/^\s*\d/.test(line),items=[];while(i<lines.length&&/^\s*(?:[-*+]\s|\d+[.)]\s)/.test(lines[i]))items.push(lines[i++].replace(/^\s*(?:[-*+]|\d+[.)])\s+/,''));const Tag=ordered?'ol':'ul';blocks.push(<Tag key={i}>{items.map((item,j)=><li key={j}><Inline text={item}/></li>)}</Tag>);continue;}
  const paragraph=[line];i++;while(i<lines.length&&lines[i].trim()&&!/^(?:#{1,6}\s|\s*```|\s*>|\s*[-*+]\s|\s*\d+[.)]\s)/.test(lines[i]))paragraph.push(lines[i++]);blocks.push(<p key={i}><Inline text={paragraph.join('\n')}/></p>);
 }
 return <div className="lw-markdown">{blocks}</div>;
}
export default function CourseContent({lesson,sources=[]}){
 const cited=sources.filter(source=>(lesson.source_ids||[]).includes(source.id));
 return <><Markdown content={lesson.content}/>{lesson.visual&&<Visual visual={lesson.visual}/>}{cited.length>0&&<section className="lw-references"><h2>Lesson references</h2><p>Material cited by your tutor. Citations do not independently verify a claim.</p><ul>{cited.map(source=><li key={source.id}>{safeCourseURL(source.url)?<a href={safeCourseURL(source.url)} target="_blank" rel="noopener noreferrer">{source.title} ↗</a>:<strong>{source.title}</strong>}<span>{source.locator||'Attached material'} · {source.read_status==='unread'?'Link · not read':source.read_status==='provided'?'Text supplied':source.read_status||'Read status unknown'}</span></li>)}</ul></section>}</>;
}
