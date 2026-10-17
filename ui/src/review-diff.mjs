import {diffLines,diffWordsWithSpace} from 'diff';

const lines=value=>value.match(/[^\n]*\n|[^\n]+$/g)||[];
// Work is bounded even for completely unrelated 50k-character lessons.
export function textDiff(before='',after='',options={}) {
 let parts=diffLines(before,after,{timeout:60,maxEditLength:1500,...options});
 const coarse=!parts;
 if(!parts)parts=[{removed:true,value:before},{added:true,value:after}];
 const rows=[],wordDeadline=Date.now()+40;
 for(let i=0;i<parts.length;i++){
  const part=parts[i],kind=part.added?'added':part.removed?'removed':'same';
  const block=lines(part.value).map(text=>({kind,text}));
  // Highlight words only within comparable replacement lines; never guess across unequal blocks.
  if(part.removed&&parts[i+1]?.added){
   const next=lines(parts[i+1].value);
   if(block.length===next.length&&block.length<=100){
    parts[i+1].wordRows=next.map((text,j)=>{
     if(Date.now()>wordDeadline||text.length+block[j].text.length>8000)return null;
     const words=diffWordsWithSpace(block[j].text,text,{timeout:10,maxEditLength:300});
     if(!words)return null;
     block[j].words=words.filter(w=>!w.added).map(w=>({text:w.value,changed:!!w.removed}));
     return words.filter(w=>!w.removed).map(w=>({text:w.value,changed:!!w.added}));
    });
   }
  }
  if(part.wordRows)block.forEach((row,j)=>{row.words=part.wordRows[j];});
  rows.push(...block);
 }
 const groups=[];
 for(let i=0;i<rows.length;){
  if(rows[i].kind!=='same'){groups.push({rows:[rows[i++]]});continue;}
  let end=i;while(end<rows.length&&rows[end].kind==='same')end++;
  const head=i>0?2:0,tail=end<rows.length?2:0;
  if(end-i>head+tail+2){
   if(head)groups.push({rows:rows.slice(i,i+head)});
   groups.push({collapsed:true,rows:rows.slice(i+head,end-tail)});
   if(tail)groups.push({rows:rows.slice(end-tail,end)});
  }else groups.push({rows:rows.slice(i,end)});
  i=end;
 }
 return {groups,coarse,added:rows.filter(r=>r.kind==='added').length,removed:rows.filter(r=>r.kind==='removed').length};
}

export function reviewEntries(course,proposal){
 const old=course.outline||[],next=proposal.outline||old;
 const saved=new Map((course.lessons||[]).map(l=>[l.key,l]));
 const supplied=new Map((proposal.lessons||[]).map(l=>[l.lesson_key||l.key,l]));
 const keys=[...next.map(l=>l.key),...old.filter(l=>!next.some(n=>n.key===l.key)).map(l=>l.key)];
 return keys.map(key=>{
  const from=old.findIndex(l=>l.key===key),to=next.findIndex(l=>l.key===key);
  const previous=old[from],outline=next[to],before=saved.get(key)||null;
  const after=to<0?null:supplied.get(key)||(proposal.mode==='regenerate'?null:before&&{...before,title:outline.title});
  const labels=[];
  if(from<0)labels.push('Added');
  if(to<0)labels.push('Removed');
  if(from>=0&&to>=0){
   if(previous.title!==outline.title)labels.push('Renamed');
   if(previous.goal!==outline.goal)labels.push('Goal updated');
   if(from!==to)labels.push('Moved');
  }
  if(supplied.has(key))labels.push(before?'Revised':'Content added');
  if(before&&!after&&to>=0)labels.push('Content cleared');
  return {key,title:outline?.title||previous.title,previous,outline,from,to,before,after,labels,changed:labels.length>0};
 });
}

function stable(value){
 if(value==null)return '';
 function sort(v){return Array.isArray(v)?v.map(sort):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,sort(v[k])])):v;}
 return JSON.stringify(sort(value),null,2);
}
export function lessonSections(before,after,sources=[]){
 const refs=lesson=>(lesson?.source_ids||[]).map(id=>{const s=sources.find(item=>item.id===id);return s?`${s.title} — ${s.url||s.locator||id}`:id;}).join('\n');
 return [
  {label:'Lesson text',before:before?.content||'',after:after?.content||''},
  ...[['Learning goals','teaching'],['Practice','practice'],['Diagram','visual']].map(([label,key])=>({label,before:stable(before?.[key]),after:stable(after?.[key])})),
  {label:'References',before:refs(before),after:refs(after)}
 ];
}
