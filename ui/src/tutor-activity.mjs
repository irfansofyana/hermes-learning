// Display only fields already exposed by the host. Never render raw tool args/results.
const text=value=>typeof value==='string'?value:'';
export const activityText=value=>text(value).slice(0,24000)+(text(value).length>24000?'\n[Display truncated]':'');
const labels={learning_course_read:'Read learning path',learning_source_read:'Read source material',learning_course_plan:'Save learning roadmap',learning_course_lesson:'Save lesson',learning_course_propose:'Propose path changes',learning_course_source:'Record source retrieval',learning_quote_check:'Check source quotation',web_search:'Search the web',web_extract:'Read web page',read_file:'Read file',todo:'Update plan',todo_write:'Update plan'};
export function toolLabel(name){return labels[name]||text(name).replaceAll('_',' ')||'Tool activity';}
export function toolActivity(payload,status='running'){
 const result=payload.result;
 const failed=result&&typeof result==='object'&&(result.error||result.success===false||result.isError===true);
 return {kind:'tool',role:'activity',toolId:text(payload.tool_id||payload.tool_call_id),name:text(payload.name),
  label:toolLabel(payload.name),status:status==='complete'&&failed?'error':status,
  detail:activityText(payload.summary||(!text(payload.name).startsWith('learning_')?payload.context||payload.preview:'')),
  duration:typeof payload.duration_s==='number'&&Number.isFinite(payload.duration_s)?Math.max(0,payload.duration_s):null};
}
export function historyReasoning(message){
 const direct=text(message.reasoning)||text(message.reasoning_content);
 if(direct)return activityText(direct);
 // Provider sidecars can also contain encrypted/opaque data; only explicit text is displayable.
 const parts=Array.isArray(message.reasoning_details)?message.reasoning_details:Array.isArray(message.codex_reasoning_items)?message.codex_reasoning_items:[];
 return activityText(parts.flatMap(part=>part?.text?[text(part.text)]:Array.isArray(part?.summary)?part.summary.map(item=>text(item?.text)):[]).filter(Boolean).join('\n\n'));
}
export function planSnapshot(payload,current){
 if(!Array.isArray(payload?.todos)||!Number.isInteger(payload.revision)||payload.revision<0||payload.revision<(current?.revision??-1))return current;
 return {revision:payload.revision,todos:payload.todos.filter(item=>item&&typeof item.content==='string').slice(0,100).map((item,index)=>({id:text(item.id)||String(index),content:item.content.slice(0,2000),status:['pending','in_progress','completed','cancelled'].includes(item.status)?item.status:'pending'}))};
}
