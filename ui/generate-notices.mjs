import {readFile,readdir,writeFile} from 'node:fs/promises';
const root=new URL('./',import.meta.url);
const lock=JSON.parse(await readFile(new URL('package-lock.json',root),'utf8'));
const sections=['# Third-party notices\n\nThe built Learning UI includes dependencies with the following license notices. Generated from the pinned UI lockfile by `npm --prefix ui run build`.'];
for(const [path,entry] of Object.entries(lock.packages).sort(([a],[b])=>a<b?-1:a>b?1:0)){
 if(!path.startsWith('node_modules/')||entry.dev)continue;
 const directory=new URL(path+'/',root),metadata=JSON.parse(await readFile(new URL('package.json',directory),'utf8'));
 const files=(await readdir(directory,{withFileTypes:true})).filter(file=>file.isFile()&&/^(?:licen[cs]e|copying|notice)(?:[._-].*)?$/i.test(file.name)).map(file=>file.name).sort();
 if(!files.length)throw new Error(`No license notice found for ${metadata.name}`);
 const licenses=await Promise.all(files.map(file=>readFile(new URL(file,directory),'utf8')));
 sections.push(`## ${metadata.name} ${metadata.version}\n\n${licenses.map(text=>text.trim()).join('\n\n')}`);
}
await writeFile(new URL('../THIRD_PARTY_NOTICES.md',root),sections.join('\n\n')+'\n');
