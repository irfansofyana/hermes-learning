import React from 'react';
import mark from './learning-mark.svg';

// Local, trusted SVG; embedded so both Hermes adapters share the same asset.
export function LearningMark() {
 return <span className="hl-mark" aria-hidden="true" dangerouslySetInnerHTML={{__html:mark}}/>;
}
