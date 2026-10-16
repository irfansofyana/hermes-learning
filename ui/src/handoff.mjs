export async function openTutorChat(host,command,storage,request='') {
 if(typeof host.newChat!=='function'||typeof host.composer?.insertText!=='function'||typeof host.composer?.getDraft!=='function')throw new Error('This host cannot prepare a chat. Copy the tutor request instead.');
 const profile=host.state?.profile?.get?.(),connection=host.state?.connectionId?.get?.();
 const stable=()=>host.state?.profile?.get?.()===profile&&host.state?.connectionId?.get?.()===connection;
 if(!/^\/learning-track resume [^\s]+$/.test(command))throw new Error('The resume command must be sent as one separate line.');
 try{storage?.setItem('hermes-learning:tutor-request',`${command}\n\n${request}`);}catch{}
 const completed=()=>{host.composer.focus?.('new');return true;};
 host.newChat();
 for(let attempt=0;attempt<8;attempt++){
  await new Promise(resolve=>setTimeout(resolve,150));
  if(!stable())throw new Error('Your Hermes profile changed. Return to Learning and copy the tutor request for the intended profile.');
  const draft=await host.composer.getDraft?.('new');
  if(!stable())throw new Error('Your Hermes profile changed while opening chat. Your request is retained in Learning.');
  if(draft?.trim()===command)return completed();
  if(draft?.trim())throw new Error('The chat composer already contains a draft. It was kept. Return to Learning to copy the resume command and send it separately.');
  const inserted=await host.composer.insertText('new',command,{mode:'block'});
  if(inserted)return completed();
 }
 throw new Error('The chat composer did not become ready. Return to Learning and copy your saved tutor request.');
}
