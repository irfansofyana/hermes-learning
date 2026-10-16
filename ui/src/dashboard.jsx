import React from 'react';
import App from './App.jsx';
const SDK=window.__HERMES_PLUGIN_SDK__;
const request=(path,body)=>SDK.fetchJSON(`/api/plugins/hermes-learning${path}`,body===undefined?{method:'GET'}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
function LearningWorkspace(){return <App request={request}/>;}
window.__HERMES_PLUGINS__.register('hermes-learning',LearningWorkspace);
