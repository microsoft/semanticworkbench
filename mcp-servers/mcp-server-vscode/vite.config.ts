import path from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
    build: {
        lib: {
            entry: './src/extension.ts',
            formats: ['cjs'],
            fileName: () => 'extension.js',
        },
        outDir: 'dist',
        minify: false,
        sourcemap: true,
        rollupOptions: {
            external: [
                'vscode',
                'net',
                'http',
                'express',
                'node:crypto',
                'crypto',
                /node:.*/, // Handle all node: protocol imports
                '@modelcontextprotocol/sdk',
            ],
            output: {
                format: 'cjs',
                entryFileNames: '[name].js',
                chunkFileNames: '[name].js',
                interop: 'compat',
            },
        },
        commonjsOptions: {
            transformMixedEsModules: true,
            include: [/node_modules\/@modelcontextprotocol\/sdk/, /\.(js|ts)$/],
        },
    },
    optimizeDeps: {
        include: ['@modelcontextprotocol/sdk'],
    },
    resolve: {
        alias: {
            '@modelcontextprotocol/sdk': path.resolve(__dirname, 'node_modules/@modelcontextprotocol/sdk/dist/esm'),
            'node:crypto': 'crypto',
        },
        extensions: ['.js', '.ts'],
    },
});
