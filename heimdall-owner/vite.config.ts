import {defineConfig,loadEnv} from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig(({mode})=>{const env=loadEnv(mode,process.cwd(),'');return {plugins:[react()],server:{proxy:{'/api':{target:env.HEIMDALL_API_ORIGIN||'http://127.0.0.1:8766',rewrite:path=>path.replace(/^\/api/,'')}}},build:{outDir:'build-owner-20261120-connected',emptyOutDir:false}}});