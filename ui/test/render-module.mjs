import {build} from 'esbuild';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
const require=createRequire(import.meta.url);
// Render bundled JSX with the same React instance as react-dom/server.
export async function loadRenderedModule(relative){
 const directory=await mkdtemp(join(tmpdir(),'learning-render-'));
 try{
  const result=await build({entryPoints:[new URL(relative,import.meta.url).pathname],bundle:true,write:false,format:'esm',platform:'node',loader:{'.jsx':'jsx'},plugins:[{name:'test-shared-react',setup(builder){builder.onResolve({filter:/^react(?:\/|$)/},args=>({path:pathToFileURL(require.resolve(args.path)).href,external:true}));}}]});
  const file=join(directory,'component.mjs');await writeFile(file,result.outputFiles[0].text);
  return await import(pathToFileURL(file).href);
 }finally{await rm(directory,{recursive:true,force:true});}
}
