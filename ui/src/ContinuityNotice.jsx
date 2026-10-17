import React from 'react';
export function ContinuityNotice({flag,busy,onReview,onKeep}){
 if(!flag)return null;
 return <aside className="lw-continuity-notice" aria-label="Lesson continuity"><strong>This lesson may need updating</strong><p>{flag.causes?.length?`${flag.causes.map(c=>c.title).join(', ')} changed.`:flag.reason} Check that its examples and explanation still fit. Your saved lesson has not been rewritten.</p><div className="lw-button-row"><button type="button" className="lw-button lw-primary" disabled={busy} onClick={onReview}>Suggest update</button><button type="button" className="lw-button" disabled={busy} onClick={onKeep}>Keep current lesson</button></div><p className="lw-continuity-help">Suggested edits appear in Changes for you to review before applying.</p></aside>;
}
