import './build-config.mjs';
import {mkdir,copyFile,cp,rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const out=root+'dist';
await rm(out,{recursive:true,force:true});await mkdir(out,{recursive:true});
for(const file of ['index.html','styles.css','config.js'])await copyFile(root+file,out+'/'+file);
await cp(root+'js',out+'/js',{recursive:true});
console.log('정적 배포 파일을 생성했습니다. 환경 파일과 테스트는 포함하지 않습니다.');
