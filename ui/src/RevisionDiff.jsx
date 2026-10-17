import React,{useMemo,useState} from 'react';
import {lessonSections,reviewEntries,textDiff} from './review-diff.mjs';

function DiffRows({rows}){
 return rows.map((row,i)=><div key={i} className={`lw-diff-line lw-diff-${row.kind}`}><span className="lw-diff-sign" aria-label={row.kind==='added'?'Added':row.kind==='removed'?'Removed':'Unchanged'}>{row.kind==='added'?'+':row.kind==='removed'?'−':' '}</span><span className="lw-diff-text">{row.words?row.words.map((word,j)=>word.changed?<mark key={j}>{word.text}</mark>:word.text):row.text}</span></div>);
}
function TextDiff({before,after}){
 const diff=useMemo(()=>textDiff(before,after),[before,after]);
 return <div className="lw-text-diff"><div className="lw-diff-counts"><span>+{diff.added} added</span><span>−{diff.removed} removed</span></div>{diff.coarse&&<p className="lw-change-note">Large rewrite: showing complete removed and added text.</p>}{diff.groups.map((group,i)=>group.collapsed?<details className="lw-diff-context" key={i}><summary>Show {group.rows.length} unchanged lines</summary><DiffRows rows={group.rows}/></details>:<DiffRows key={i} rows={group.rows}/>)}</div>;
}
function EntryReview({entry,sources,Preview}){
 const [view,setView]=useState('changes');
 const sections=useMemo(()=>lessonSections(entry.before,entry.after,sources),[entry,sources]);
 const changed=sections.filter(s=>s.before!==s.after);
 const roadmapBefore=entry.previous?`${entry.previous.title}\n${entry.previous.goal}`:'';
 const roadmapAfter=entry.outline?`${entry.outline.title}\n${entry.outline.goal}`:'';
 return <section className="lw-diff-detail" aria-label={`Changes to ${entry.title}`}>
  <header className="lw-diff-heading"><div><h3>{entry.title}</h3><p>{entry.labels.join(' · ')||'Unchanged'}{entry.from>=0&&entry.to>=0&&entry.from!==entry.to?` · Lesson ${entry.from+1} → ${entry.to+1}`:''}</p></div><div className="lw-diff-switch" role="group" aria-label="Review view">{['changes','preview'].map(mode=><button key={mode} type="button" aria-pressed={view===mode} onClick={()=>setView(mode)}>{mode==='changes'?'Changes':'Preview'}</button>)}</div></header>
  {view==='changes'?<>
   {roadmapBefore!==roadmapAfter&&<section className="lw-diff-section"><h4>Roadmap</h4><TextDiff before={roadmapBefore} after={roadmapAfter}/></section>}
   {changed.map(s=><section className="lw-diff-section" key={s.label}><h4>{s.label}</h4><TextDiff before={s.before} after={s.after}/></section>)}
   {!changed.length&&<p className="lw-change-note">{entry.before||entry.after?'Lesson content is unchanged.':'This lesson has no generated content yet.'}</p>}
   {entry.labels.includes('Content cleared')&&<p className="lw-change-warning">The saved lesson content will be removed. A new lesson will be generated when you open it.</p>}
   {entry.labels.includes('Revised')&&!changed.length&&<p className="lw-change-note">This lesson was resubmitted and will be marked unread when applied.</p>}
   {changed.some(s=>s.label==='Lesson text'||s.label==='Diagram')&&<p className="lw-change-note">Open Preview to compare rendered lessons, diagrams, and images.</p>}
  </>:<div className="lw-diff-previews">{[['Current',entry.before,entry.previous],['Proposed',entry.after,entry.outline]].map(([label,lesson,outline])=><section key={label} aria-label={`${label} lesson preview`}><h4>{label}</h4>{outline&&<><h3>{outline.title}</h3><p>{outline.goal}</p></>}{lesson?<Preview lesson={lesson} sources={sources}/>:<p className="lw-change-note">{outline?'Content will be generated when opened.':label==='Current'?'New lesson.':'Removed from the path.'}</p>}</section>)}</div>}
 </section>;
}
export default function RevisionDiff({course,proposal,Preview}){
 const entries=useMemo(()=>reviewEntries(course,proposal),[course,proposal]);
 const changed=entries.filter(e=>e.changed),unchanged=entries.filter(e=>!e.changed);
 const [selected,setSelected]=useState(null);
 const entry=entries.find(e=>e.key===selected)||changed[0]||entries[0];
 const counts=[['added',changed.filter(e=>e.from<0).length],['updated',changed.filter(e=>e.from>=0&&e.to>=0).length],['removed',changed.filter(e=>e.to<0).length]].filter(([,count])=>count);
 const item=e=><button type="button" key={e.key} aria-current={entry?.key===e.key?'true':undefined} onClick={()=>setSelected(e.key)}><span>{e.to>=0?String(e.to+1).padStart(2,'0'):'−'} · {e.title}</span><small>{e.labels.join(' · ')||'Unchanged'}</small></button>;
 return <section className="lw-revision-diff" aria-label="Revision comparison"><p className="lw-diff-overview">{counts.map(([label,count])=>`${count} ${label}`).join(' · ')||'No content changes'}{unchanged.length?` · ${unchanged.length} unchanged`:''}</p><div className="lw-diff-layout"><nav className="lw-diff-nav" aria-label="Lessons in this revision">{changed.map(item)}{unchanged.length>0&&<details><summary>{unchanged.length} unchanged lessons</summary>{unchanged.map(item)}</details>}</nav>{entry&&<EntryReview key={entry.key} entry={entry} sources={course.sources} Preview={Preview}/>}</div></section>;
}
