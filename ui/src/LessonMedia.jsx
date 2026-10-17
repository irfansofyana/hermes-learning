import React,{createContext,useContext,useEffect,useLayoutEffect,useRef,useState} from 'react';
import {assetId,renderMermaid} from './lesson-media.mjs';
import {CodeBlock} from './CodeBlock.jsx';
import {Icon} from './icons.jsx';
export const LessonMediaContext=createContext(null);
const mediaError=(error,fallback)=>/Unknown learning action/i.test(error?.message||'')?'Update the Learning plugin on the Hermes backend to enable this media feature. Your saved source is kept.':error?.message||fallback;

function MediaViewer({src,title,caption}){
 const [large,setLarge]=useState(false),[zoom,setZoom]=useState(1),[failed,setFailed]=useState(false);
 const dialog=useRef(null);
 useEffect(()=>{setFailed(false);setZoom(1);},[src]);
 useLayoutEffect(()=>{if(!large)return;const node=dialog.current;node.showModal();return()=>node.close();},[large]);
 const picture=<img src={src} alt={title} draggable={false} onError={()=>setFailed(true)}/>;
 return <div className="lw-media-viewer">{failed?<p role="alert">This image could not be displayed.</p>:<><button type="button" className="lw-media-open" aria-label={`Enlarge ${title}`} onClick={()=>{setZoom(1);setLarge(true);}}>{picture}</button><div className="lw-media-caption"><span>{caption||title}</span><button type="button" className="lw-icon-button" aria-label={`Enlarge ${title}`} onClick={()=>setLarge(true)}><Icon name="expand" size={16}/></button></div></>}{large&&<dialog ref={dialog} className="lw-media-dialog" aria-label={title} onCancel={e=>{e.preventDefault();e.stopPropagation();setLarge(false);}} onClick={e=>{if(e.target===dialog.current)setLarge(false);}}><header><strong>{title}</strong><div><button type="button" aria-label="Zoom out" disabled={zoom<=0.5} onClick={()=>setZoom(z=>Math.max(.5,z-.25))}>−</button><button type="button" onClick={()=>setZoom(1)}>Fit</button><button type="button" aria-label="Zoom in" disabled={zoom>=4} onClick={()=>setZoom(z=>Math.min(4,z+.25))}>+</button><button type="button" aria-label="Close image" onClick={()=>setLarge(false)}><Icon name="close"/></button></div></header><div className="lw-media-pan" tabIndex={0} aria-label="Diagram viewport; scroll to pan"><img src={src} alt={title} style={{width:`${zoom*100}%`}}/></div></dialog>}</div>;
}

export function DiagramBlock({language,source}){
 const media=useContext(LessonMediaContext),[result,setResult]=useState(null),[error,setError]=useState(''),[retry,setRetry]=useState(0);
 const isArchify=language==='archify';
 useEffect(()=>{
  let current=true;setResult(null);setError('');
  // The source is saved in Markdown; only derived rendering is asynchronous.
  const render=async()=>{
   if(!isArchify)return {src:await renderMermaid(source,()=>current),title:'Mermaid diagram'};
   if(!media?.contextId)throw Error('Open this learning path to render its Archify diagram.');
   const value=await media.request('/action',{api_version:1,action:'course_diagram_render',params:{context_id:media.contextId,source}});
   if(value.mime!=='image/svg+xml'||typeof value.data!=='string'||value.data.length>3000000)throw Error('Archify returned an unsupported image.');
   return {src:`data:${value.mime};base64,${value.data}`,title:value.title||'Archify diagram'};
  };
  const timer=setTimeout(()=>render().then(value=>{if(current)setResult(value);},e=>{if(current)setError(mediaError(e,'Diagram rendering failed.'));}),250);
  return()=>{current=false;clearTimeout(timer);};
 },[source,isArchify,media?.request,media?.contextId,retry]);
 return <section className="lw-media-block" aria-label={`${isArchify?'Archify':'Mermaid'} diagram`}><div className="lw-media-label">{isArchify?'Archify':'Mermaid'}</div>{error?<div className="lw-media-error" role="alert"><p>{error}</p><button type="button" className="lw-button" onClick={()=>setRetry(v=>v+1)}>Retry diagram</button></div>:result?<MediaViewer src={result.src} title={result.title}/>:<p className="lw-media-loading" role="status">Rendering diagram…</p>}<details className="lw-media-source" open={!!error}><summary>Diagram source</summary><CodeBlock code={source} language={isArchify?'json':'mermaid'}/></details></section>;
}

export function SavedImage({src,alt}){
 const media=useContext(LessonMediaContext),[result,setResult]=useState(null),[error,setError]=useState(''),[retry,setRetry]=useState(0);
 const id=assetId(src);
 useEffect(()=>{
  let current=true;setResult(null);setError('');
  if(!id||!media?.trackId){setError('Open the image’s learning path to view it.');return;}
  media.request('/action',{api_version:1,action:'course_asset_read',params:{track_id:media.trackId,asset_id:id}}).then(value=>{
   if(!['image/png','image/jpeg'].includes(value.mime)||typeof value.data!=='string'||value.data.length>7100000)throw Error('Unsupported saved image.');
   if(current)setResult(value);
  }).catch(e=>{if(current)setError(mediaError(e,'The image could not be loaded.'));});
  return()=>{current=false;};
 },[id,media?.request,media?.trackId,retry]);
 return <div className="lw-saved-image">{error?<span role="alert">{error} <button type="button" onClick={()=>setRetry(v=>v+1)}>Retry image</button></span>:result?<MediaViewer src={`data:${result.mime};base64,${result.data}`} title={alt&&alt!=='Saved image'?alt:result.title} caption={result.title}/>:<span role="status">Loading image…</span>}</div>;
}
