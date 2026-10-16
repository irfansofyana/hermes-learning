export async function previewRequest(path,body) {
 const response=await fetch(`/api/plugins/hermes-learning${path}`,body===undefined?{credentials:'same-origin'}:{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const data=await response.json();
 if(!response.ok){const error=new Error(typeof data.detail==='string'?data.detail:typeof data.error==='string'?data.error:data.message||`Request failed (${response.status}).`);error.status=response.status;error.code=data.code;throw error;}
 return data;
}
