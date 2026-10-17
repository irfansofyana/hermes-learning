export function practiceDraftKey(scope, track, lesson) {
 return `learning-practice:${encodeURIComponent(scope)}:${track}:${lesson.id}:${lesson.version||1}`;
}
export function readPracticeDraft(storage, key) {
 try {
  const value=JSON.parse(storage?.getItem(key)||'null');
  if(value&&typeof value.answer==='string')return {answer:value.answer.slice(0,20000),hints:Math.max(0,Math.min(5,Math.floor(Number(value.hints)||0))),revealed:!!value.revealed,skipped:!!value.skipped};
 }catch{}
 return {answer:'',hints:0,revealed:false,skipped:false};
}
export function writePracticeDraft(storage,key,value) {
 try{storage?.setItem(key,JSON.stringify(value));return true;}catch{return false;}
}
export function practiceTutorMessage(lesson, answer, feedback) {
 return `Help me understand this optional practice from “${lesson.title}”.\n\nExercise:\n${lesson.practice.prompt}\n\nMy answer:\n${answer||'(Not attempted yet)'}${feedback?`\n\nPractice feedback:\n${feedback}`:''}\n\nDiscuss this with me; do not change the saved lesson unless I ask.`;
}
