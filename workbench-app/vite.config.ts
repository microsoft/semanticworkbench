import replace from '@rollup/plugin-replace';
import react from '@vitejs/plugin-react';
import fs from 'fs';
import path from 'path';
import { defineConfig } from 'vite';
import mkcert from 'vite-plugin-mkcert';

const packageJson = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'package.json'), 'utf8'));
const dateString = new Date().toISOString().replace('T', ' @ ').replace(/\..+/, '');
const appVersion = `${packageJson.version as string} (${dateString})`;
const replaceOptions = {
    __APP_VERSION__: appVersion,
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV),
    preventAssignment: true,
};

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        react(),
        replace(replaceOptions),
        mkcert({
            savePath: 'certs',
            keyFileName: 'key.pem',
            certFileName: 'cert.pem',
        }),
    ],
    server: {
        https: {},
        host: '127.0.0.1',
        port: JSON.parse(process.env.PORT || '4000'),
    },
    build: {
        outDir: 'build',
        sourcemap: true,
    },
});
