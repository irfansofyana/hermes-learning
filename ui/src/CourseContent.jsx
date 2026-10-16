import React from 'react';
import {Visual} from './Visual.jsx';

export function safeCourseURL(value){
 try{const url=new URL(value);return ['https:','http:'].includes(url.protocol)?url.href:null;}catch{return null;}
}
function Inline({text}){
 // React escapes every source token. Raw HTML, images, and executable URLs are never interpreted.
 const parts=String(text).split(/(\uE200cite\uE202[^\uE201\r\n]*\uE201|`[^`\n]+`|\*\*[^*\n]+\*\*|\*[^*\n]+\*|\[[^\]\n]+\]\([^\s)]+\))/g);
 return parts.map((part,i)=>{
  if(part.startsWith('\uE200cite\uE202'))return <span key={i} className="lw-citation-unavailable" title="The tutor saved this citation without its source URL.">[Source link unavailable]</span>;
  if(part.startsWith('`')&&part.endsWith('`'))return <code key={i}>{part.slice(1,-1)}</code>;
  if(part.startsWith('**')&&part.endsWith('**'))return <strong key={i}><Inline text={part.slice(2,-2)}/></strong>;
  if(part.startsWith('*')&&part.endsWith('*'))return <em key={i}><Inline text={part.slice(1,-1)}/></em>;
  const link=part.match(/^\[([^\]]+)\]\(([^)]+)\)$/),href=link&&safeCourseURL(link[2]);
  if(href)return <a key={i} href={href} target="_blank" rel="noopener noreferrer">{link[1]}</a>;
  return part;
 });
}
function tableRow(line){
 const text=line.trim(),cells=[];let cell='',pipes=0;
 for(let i=0;i<text.length;i++){
  if(text[i]==='\\'&&text[i+1]==='|'){cell+='|';i++;}
  else if(text[i]==='\\'&&text[i+1]==='\\'){cell+='\\\\';i++;}
  else if(text[i]==='|'){cells.push(cell.trim());cell='';pipes++;}
  else cell+=text[i];
 }
 cells.push(cell.trim());
 if(text.startsWith('|'))cells.shift();
 if(text.endsWith('|')&&cells.at(-1)==='')cells.pop();
 return {cells,pipes};
}
function tableHeader(lines,index){
 if(index+1>=lines.length)return null;
 const header=tableRow(lines[index]),divider=tableRow(lines[index+1]);
 if(!(header.pipes||divider.pipes)||!header.cells.length||header.cells.length!==divider.cells.length||!divider.cells.every(cell=>/^:?-{3,}:?$/.test(cell)))return null;
 return {headers:header.cells,alignments:divider.cells.map(cell=>cell.startsWith(':')?cell.endsWith(':')?'center':'left':cell.endsWith(':')?'right':undefined)};
}
export function Markdown({content=''}){
 const lines=String(content).replace(/\r\n/g,'\n').split('\n'),blocks=[];
 for(let i=0;i<lines.length;){
  const line=lines[i];
  if(!line.trim()){i++;continue;}
  if(/^\s*```/.test(line)){const language=line.trim().slice(3),code=[];i++;while(i<lines.length&&!/^\s*```/.test(lines[i]))code.push(lines[i++]);if(i<lines.length)i++;blocks.push(<div className="lw-code-block" key={i}>{language&&<div className="lw-code-language">{language}</div>}<pre><code>{code.join('\n')}</code></pre></div>);continue;}
  const table=tableHeader(lines,i);
  if(table){
   const rows=[];i+=2;
   while(i<lines.length&&lines[i].trim()&&!/^\s*(?:#{1,6}\s|```|>|[-*+]\s|\d+[.)]\s)/.test(lines[i])&&tableRow(lines[i]).pipes){rows.push(tableRow(lines[i++]).cells);}
   blocks.push(<div className="lw-table-wrap" role="region" aria-label="Lesson table" tabIndex={0} key={i}><table><thead><tr>{table.headers.map((header,j)=><th key={j} scope="col" style={{textAlign:table.alignments[j]}}><Inline text={header}/></th>)}</tr></thead><tbody>{rows.map((row,k)=><tr key={k}>{table.headers.map((_,j)=><td key={j} style={{textAlign:table.alignments[j]}}><Inline text={row[j]||''}/></td>)}</tr>)}</tbody></table></div>);continue;
  }
  const heading=line.match(/^(#{1,6})\s+(.+)$/);
  if(heading){const Tag=`h${Math.min(heading[1].length+1,6)}`;blocks.push(<Tag key={i}><Inline text={heading[2]}/></Tag>);i++;continue;}
  if(/^\s*([-*_])(?:\s*\1){2,}\s*$/.test(line)){blocks.push(<hr key={i++}/>);continue;}
  if(/^\s*>\s?/.test(line)){const quote=[];while(i<lines.length&&/^\s*>/.test(lines[i]))quote.push(lines[i++].replace(/^\s*>\s?/,''));blocks.push(<blockquote key={i}><Inline text={quote.join(' ')}/></blockquote>);continue;}
  if(/^\s*(?:[-*+]\s|\d+[.)]\s)/.test(line)){const ordered=/^\s*\d/.test(line),items=[];while(i<lines.length&&/^\s*(?:[-*+]\s|\d+[.)]\s)/.test(lines[i]))items.push(lines[i++].replace(/^\s*(?:[-*+]|\d+[.)])\s+/,''));const Tag=ordered?'ol':'ul';blocks.push(<Tag key={i}>{items.map((item,j)=><li key={j}><Inline text={item}/></li>)}</Tag>);continue;}
  const paragraph=[line];i++;while(i<lines.length&&lines[i].trim()&&!tableHeader(lines,i)&&!/^(?:#{1,6}\s|\s*```|\s*>|\s*[-*+]\s|\s*\d+[.)]\s)/.test(lines[i]))paragraph.push(lines[i++]);blocks.push(<p key={i}><Inline text={paragraph.join('\n')}/></p>);
 }
 return <div className="lw-markdown">{blocks}</div>;
}
export default function CourseContent({lesson,sources=[]}){
 const cited=sources.filter(source=>(lesson.source_ids||[]).includes(source.id));
 return <><Markdown content={lesson.content}/>{lesson.visual&&<Visual visual={lesson.visual}/>}{cited.length>0&&<section className="lw-references"><h2>Lesson references</h2><p>Material cited by your tutor. Citations do not independently verify a claim.</p><ul>{cited.map(source=><li key={source.id}>{safeCourseURL(source.url)?<a href={safeCourseURL(source.url)} target="_blank" rel="noopener noreferrer">{source.title} ↗</a>:<strong>{source.title}</strong>}<span>{source.locator||'Attached material'} · {source.read_status==='unread'?'Link · not read':source.read_status==='provided'?'Text supplied':source.read_status||'Read status unknown'}</span></li>)}</ul></section>}</>;
}
