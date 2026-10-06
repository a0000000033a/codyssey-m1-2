import {writeFileSync,existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
const envPath=fileURLToPath(new URL('../.env',import.meta.url));
if(existsSync(envPath)) process.loadEnvFile(envPath);
const config={apiBaseUrl:process.env.API_BASE_URL || 'http://127.0.0.1:8000',firebase:{
  apiKey:process.env.FIREBASE_API_KEY || '',authDomain:process.env.FIREBASE_AUTH_DOMAIN || '',projectId:process.env.FIREBASE_PROJECT_ID || ''}};
const output=process.argv[2] || fileURLToPath(new URL('../config.js',import.meta.url));
writeFileSync(output,`window.APP_CONFIG = ${JSON.stringify(config).replace(/</g,'\\u003c')};\n`);
console.log('공개 프론트 설정을 생성했습니다.');
