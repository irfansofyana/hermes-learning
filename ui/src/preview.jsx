import React from 'react';
import {createRoot} from 'react-dom/client';
import App from './App.jsx';
import {previewRequest} from './transport.mjs';
createRoot(document.getElementById('root')).render(<App request={previewRequest} preview/>);
