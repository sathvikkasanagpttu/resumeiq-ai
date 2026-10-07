import { build } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));

async function run() {
  console.log('Building ResumeIQ Extension (Single Source of Truth: dist/)...');
  
  const isProd = process.env.NODE_ENV === 'production';
  const apiBaseUrl = process.env.VITE_API_URL || (isProd ? 'https://api.resumeiq.ai/api/v1' : 'http://localhost:8000/api/v1');
  const sharedDefines = {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || (isProd ? 'production' : 'development')),
    'process.env.VITE_API_URL': JSON.stringify(apiBaseUrl),
  };

  // 1. Build Side Panel React Application
  console.log('Building sidepanel...');
  await build({
    configFile: false,
    base: './',
    define: sharedDefines,
    plugins: [react()],
    root: resolve(__dirname, 'src/sidepanel'),
    build: {
      outDir: resolve(__dirname, 'dist'),
      emptyOutDir: true,
      rollupOptions: {
        input: {
          sidepanel: resolve(__dirname, 'src/sidepanel/index.html'),
        },
      },
    },
  });

  // Ensure dist/sidepanel.html exists
  const distIndex = resolve(__dirname, 'dist/index.html');
  const distSidepanel = resolve(__dirname, 'dist/sidepanel.html');
  if (fs.existsSync(distIndex) && !fs.existsSync(distSidepanel)) {
    fs.copyFileSync(distIndex, distSidepanel);
  }

  // 2. Build Background Service Worker (ES module)
  console.log('Building background service worker...');
  await build({
    configFile: false,
    define: sharedDefines,
    build: {
      outDir: resolve(__dirname, 'dist'),
      emptyOutDir: false,
      lib: {
        entry: resolve(__dirname, 'src/background/service-worker.ts'),
        formats: ['es'],
        fileName: () => 'background.js',
      },
    },
  });

  // 3. Build Content Script (IIFE, self-contained)
  console.log('Building content script...');
  await build({
    configFile: false,
    define: sharedDefines,
    build: {
      outDir: resolve(__dirname, 'dist'),
      emptyOutDir: false,
      lib: {
        entry: resolve(__dirname, 'src/content/content-script.ts'),
        formats: ['iife'],
        name: 'ResumeIQContent',
        fileName: () => 'content.js',
      },
    },
  });

  // 4. Copy manifest.json and icons to dist
  console.log('Copying manifest and icons to dist...');
  fs.copyFileSync(
    resolve(__dirname, 'manifest.json'),
    resolve(__dirname, 'dist/manifest.json')
  );

  const iconsDir = resolve(__dirname, 'dist/icons');
  if (!fs.existsSync(iconsDir)) {
    fs.mkdirSync(iconsDir, { recursive: true });
  }
  for (const size of [16, 48, 128]) {
    fs.copyFileSync(
      resolve(__dirname, `icons/icon-${size}.png`),
      resolve(iconsDir, `icon-${size}.png`)
    );
  }

  console.log('ResumeIQ Extension build complete in dist/!');
  console.log('Unpacked extension path: ' + resolve(__dirname, 'dist'));
}

run().catch((err) => {
  console.error('Build failed:', err);
  process.exit(1);
});
