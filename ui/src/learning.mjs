export const SOURCE_MAX_BYTES = 200 * 1024;
export const SOURCE_MAX_CHARS = 50000;
export const SOURCE_EXTENSIONS = ['txt','md','markdown','rst','py','js','jsx','ts','tsx','mjs','cjs','json','yaml','yml','toml','csv','sql','html','css','go','rs','java','c','h','cpp','hpp','sh','rb','swift','kt'];
export const SOURCE_ACCEPT = SOURCE_EXTENSIONS.map(ext=>`.${ext}`).join(',');

export async function readSourceFile(file) {
 if (!file || typeof file.arrayBuffer !== 'function') throw new Error('Choose a text, Markdown, or code file.');
 const extension = file.name.split('.').at(-1).toLowerCase();
 if (!SOURCE_EXTENSIONS.includes(extension)) throw new Error('Choose a supported text, Markdown, or code file. PDF and image import are not available.');
 if (file.size > SOURCE_MAX_BYTES) throw new Error('This file is larger than 200 KB. Select a smaller excerpt first.');
 const buffer = await file.arrayBuffer();
 if (buffer.byteLength > SOURCE_MAX_BYTES) throw new Error('This file is larger than 200 KB.');
 let excerpt;
 try { excerpt = new TextDecoder('utf-8', {fatal:true}).decode(buffer); }
 catch { throw new Error('This file is not valid UTF-8 text. Save a UTF-8 copy and select it again.'); }
 if (excerpt.includes('\0')) throw new Error('This file contains binary data. Choose a plain text file.');
 if (excerpt.length > SOURCE_MAX_CHARS) throw new Error('This file exceeds 50,000 characters. Select a smaller excerpt first.');
 if (!excerpt.trim()) throw new Error('This file is empty. Choose a file with text to study.');
 return {title:file.name,locator:`File: ${file.name}`,excerpt,kind:['txt','md','markdown','rst','csv'].includes(extension)?'notes':'repository'};
}

export const visibleSteps = visual => Array.isArray(visual?.steps) ? visual.steps.slice(0,Number.isInteger(visual.visible_steps)?Math.max(0,visual.visible_steps):visual.steps.length) : [];
export const weakestOutcome = results => ['needs-work','developing','demonstrated'].find(outcome=>results.some(result=>result.outcome===outcome)) || 'developing';
export const answerLabels = kind => ({prediction:['Your prediction','Predict what happens and explain why…'],trace:['Your trace','Walk through each step and the values that change…'],build:['Your implementation','Describe your implementation, paste the relevant code, and explain how you checked it…'],explanation:['Your explanation','Explain the idea in your own words, with an example…']}[kind]||['Your answer','Walk through your reasoning…']);
export const tutorResumeCommand = track => `/learning-track resume ${track.id}`;

export function tutorPrompt(track, request={}) {
 const action = request.kind || (track.status==='active'?'resume':'proposal');
 const task = {
  proposal:'Help me clarify a small first direction. Ask one useful question at a time, use my learner profile, and suggest sources I can inspect before adding.',
  assessment:'Review the exact saved answer against its immutable criteria. Give criterion-level feedback, state uncertainty, and record an agent assessment. Do not substitute a new answer for mine.',
  dispute:'Inspect the disputed assessment and its evidence. Explain the issue and, if a correction is warranted, save a superseding assessment without erasing the original.',
  author:'Choose an objective using the saved evidence. Create one source-grounded activity with objective links, a purpose, competency, and criteria. Use a new problem to check transfer when appropriate.',
  review:'Review this objective with a different example where possible. Check the saved assistance and assessments before choosing an activity.',
  hint:'Give one useful hint for this activity. Record the exact generated help with the active run and a stable request ID before continuing. Do not reveal the full solution unless I ask.',
  resume:'Read the saved next action and continue one step at a time. Use the learner profile, source-sharing rules, and evidence to decide what comes next.'
 }[action] || 'Continue this activity one step at a time using the saved evidence.';
 const ids = [['Track',track.id],['Activity',request.activity_id],['Attempt',request.attempt_id],['Assessment',request.assessment_id],['Objective',request.objective_id],['Run',request.run_id]].filter(([,id])=>id).map(([label,id])=>`${label}: ${id}`).join('\n');
 return `Continue my learning track “${track.title}”. Read its saved resume brief.\n${ids}\n${task}\nRespect source-sharing policy. Ask before revealing a solution. This request is not an answer to an activity.`;
}
