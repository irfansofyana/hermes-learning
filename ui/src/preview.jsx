import React from 'react';
import {createRoot} from 'react-dom/client';
import LearningApp from './LearningApp.jsx';
import {previewRequest} from './transport.mjs';
import {createPreviewTutor} from './preview-tutor.mjs';
const transport=createPreviewTutor(previewRequest);
createRoot(document.getElementById('root')).render(<LearningApp request={previewRequest} transport={transport} scope="preview" preview/>);
