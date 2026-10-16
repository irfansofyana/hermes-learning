import React,{useMemo,useState,useEffect,useRef} from 'react';
import {common,createLowlight} from 'lowlight';
const highlighter=createLowlight(common);
function tokenLines(node,path='token'){
 if(node.type==='text')return node.value.split('\n').map(value=>[value]);
 const lines=[[]];
 for(const [index,child] of (node.children||[]).entries()){
  const childLines=tokenLines(child,`${path}-${index}`);
  lines[lines.length-1].push(...childLines[0]);
  for(const line of childLines.slice(1))lines.push(line);
 }
 if(node.type==='element')return lines.map((line,index)=>[<span key={`${path}-${index}`} className={(node.properties?.className||[]).join(' ')}>{line}</span>]);
 return lines;
}
export function codeLanguage(value=''){
 return String(value).trim().split(/\s+/)[0].toLowerCase().slice(0,40);
}
export function HighlightedCode({code='',language='',activeLine,lineNumbers=false}){
 const text=String(code),lang=codeLanguage(language);
 const lines=useMemo(()=>{
  if(lang&&highlighter.registered(lang)){
   try{return tokenLines(highlighter.highlight(lang,text));}catch{/* Incomplete or unsupported code remains readable. */}
  }
  return text.split('\n').map(line=>[line]);
 },[text,lang]);
 return <code className={`hljs${lang?` language-${lang}`:''}`}>{lines.map((line,index)=><React.Fragment key={index}>{index>0&&'\n'}<span className={`lw-code-line${activeLine===index+1?' is-current':''}`} aria-current={activeLine===index+1?'step':undefined}>{lineNumbers&&<span className="hl-line-number" aria-hidden="true">{index+1}</span>}{line}</span></React.Fragment>)}</code>;
}
export function CodeBlock({code='',language=''}){
 const [status,setStatus]=useState(''),timer=useRef(null),text=String(code),lang=codeLanguage(language),revision=useRef(0),current=useRef({text,lang});
 if(current.current.text!==text||current.current.lang!==lang){current.current={text,lang};revision.current++;}
 useEffect(()=>{setStatus('');return()=>{revision.current++;clearTimeout(timer.current);};},[text,lang]);
 async function copy(){
  const version=revision.current;
  try{await navigator.clipboard.writeText(text);if(version!==revision.current)return;setStatus('Copied');clearTimeout(timer.current);timer.current=setTimeout(()=>{if(version===revision.current)setStatus('');},2000);}
  catch{if(version===revision.current)setStatus('Select the code to copy it.');}
 }
 return <div className="lw-code-block"><div className="lw-code-language"><span>{lang||'Text'}</span><span className="lw-code-copy-status" role="status">{status}</span><button type="button" onClick={copy} aria-label="Copy code">{status==='Copied'?'Copied':'Copy code'}</button></div><pre tabIndex={0} aria-label={`${lang||'Text'} code example`}><HighlightedCode code={text} language={lang}/></pre></div>;
}
