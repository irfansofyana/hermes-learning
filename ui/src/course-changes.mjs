export function describeChanges(course,proposal) {
 const previous=course?.outline||[],outline=proposal.outline||previous;
 const rewritten=new Set((proposal.lessons||[]).map(lesson=>lesson.lesson_key||lesson.key));
 const rows=outline.map((item,index)=>{
  const oldIndex=previous.findIndex(old=>old.key===item.key),old=previous[oldIndex];
  const status=!old?'New':proposal.mode==='regenerate'||rewritten.has(item.key)?'Rewrite':old.title!==item.title||old.goal!==item.goal?'Updated':oldIndex!==index?'Moved':'Unchanged';
  return {...item,status,...(old?{previous:old,previousIndex:oldIndex}:{} )};
 });
 return {rows,removed:previous.filter(item=>!outline.some(next=>next.key===item.key)),resetProgress:proposal.mode==='regenerate'};
}
export function changeRequest(kind,instructions,lesson) {
 const detail=instructions.trim();
 if(!detail)throw Error('Describe what you want to change.');
 if(kind==='lesson'&&!lesson)throw Error('Choose a lesson to revise.');
 const mode=kind==='extend'||kind==='regenerate'?kind:'revise';
 const prefix={lesson:`Revise the lesson “${lesson?.title}”`,roadmap:'Adjust my learning roadmap',extend:'Extend my learning path',regenerate:'Regenerate my learning path'}[kind];
 if(!prefix)throw Error('Choose a supported change.');
 return {mode,target:kind==='lesson'?'lesson':'path',...(kind==='lesson'?{lesson_key:lesson.key}:{}),message:`${prefix}: ${detail}`};
}
