import DOMPurify from 'dompurify';
let sequence=Promise.resolve(),serial=0;
export function checkedMermaid(source){
 if(typeof source!=='string'||!source.trim()||source.length>30000)throw Error('Use a Mermaid diagram of at most 30,000 characters.');
 if(/\b(?:img|icon)\s*:|<(?:img|iframe|script|style|link|object|embed)\b/i.test(source))throw Error('Embedded images and HTML are not supported in Mermaid. Use a saved lesson image instead.');
 if(/(?:^|[;\n])\s*(?:classDef|style|linkStyle|click)\b/i.test(source))throw Error('Custom CSS and click handlers are not supported in lesson diagrams. Use the default diagram styling.');
 if(/^\s*---|%%\s*\{|\b(?:https?:|javascript:|data:|file:)|url\s*\(/im.test(source))throw Error('Diagram configuration directives and external resources are not supported. Keep only the diagram definition.');
 return source;
}
export function renderMermaid(source,isCurrent=()=>true){
 const run=async()=>{
  if(!isCurrent())throw Error('Rendering cancelled.');
  checkedMermaid(source);
  const {default:mermaid}=await import('mermaid');
  mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'default',htmlLabels:false,maxTextSize:30000,maxEdges:200,suppressErrorRendering:true,flowchart:{useMaxWidth:false},sequence:{useMaxWidth:false},fontFamily:'Arial, sans-serif'});
  const id=`learning-diagram-${++serial}`;
  try{
   const {svg}=await mermaid.render(id,source);
   const safe=DOMPurify.sanitize(svg,{USE_PROFILES:{svg:true,svgFilters:true},FORBID_TAGS:['foreignObject','a','image','script'],ADD_ATTR:['xmlns']});
   return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(safe)}`;
  }finally{document.getElementById(id)?.remove();document.getElementById('d'+id)?.remove();}
 };
 const result=sequence.then(run,run);sequence=result.catch(()=>{});return result;
}
export function assetId(url){return /^learning-asset:([a-zA-Z0-9_-]{1,100})$/.exec(url||'')?.[1]||null;}
