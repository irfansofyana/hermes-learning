import {readFile,readdir,writeFile} from 'node:fs/promises';
const root=new URL('./',import.meta.url);
const lock=JSON.parse(await readFile(new URL('package-lock.json',root),'utf8'));
const sections=['# Third-party notices\n\nThe built Learning UI includes dependencies with the following license notices. Generated from the pinned UI lockfile by `npm --prefix ui run build`.'];
for(const [path,entry] of Object.entries(lock.packages).sort(([a],[b])=>a<b?-1:a>b?1:0)){
 if(!path.startsWith('node_modules/')||entry.dev)continue;
 const directory=new URL(path+'/',root),metadata=JSON.parse(await readFile(new URL('package.json',directory),'utf8'));
 const files=(await readdir(directory,{withFileTypes:true})).filter(file=>file.isFile()&&/^(?:licen[cs]e|copying|notice)(?:[._-].*)?$/i.test(file.name)).map(file=>file.name).sort();
 const licenses=await Promise.all(files.map(file=>readFile(new URL(file,directory),'utf8')));
 if(!licenses.length){const readme=await readFile(new URL('README.md',directory),'utf8');const license=/^## License\s*\n([\s\S]*?)(?=^## |$(?![\s\S]))/im.exec(readme)?.[1];if(!license?.includes('Permission is hereby granted'))throw new Error(`No license notice found for ${metadata.name}`);licenses.push(license);}
 sections.push(`## ${metadata.name} ${metadata.version}\n\n${licenses.map(text=>text.trim()).join('\n\n')}`);
}
sections.push('## Archify 2.16.0 (vendored backend renderer)\n\n'+await readFile(new URL('../vendor/archify/LICENSE',root),'utf8'));
await writeFile(new URL('../THIRD_PARTY_NOTICES.md',root),sections.join('\n\n').replace(/[ \t]+$/gm,'').trimEnd()+'\n');
