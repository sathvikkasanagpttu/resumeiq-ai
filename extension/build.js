import { build } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));

function copyDirSync(src, dest) {
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = resolve(src, entry.name);
    const destPath = resolve(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

async function run() {
  console.log('Building ResumeIQ Extension...');
  
  // 1. Build Side Panel React Application
  console.log('Building sidepanel...');
  await build({
    configFile: false,
    base: './',
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

  // 5. Ensure extension root directory also has all required files so Chrome can load EITHER root or dist/
  console.log('Syncing compiled bundles to extension root for direct loading...');
  fs.copyFileSync(resolve(__dirname, 'dist/background.js'), resolve(__dirname, 'background.js'));
  fs.copyFileSync(resolve(__dirname, 'dist/content.js'), resolve(__dirname, 'content.js'));
  fs.copyFileSync(resolve(__dirname, 'dist/sidepanel.html'), resolve(__dirname, 'sidepanel.html'));
  const rootAssetsDir = resolve(__dirname, 'assets');
  if (fs.existsSync(rootAssetsDir)) {
    fs.rmSync(rootAssetsDir, { recursive: true, force: true });
  }
  if (fs.existsSync(resolve(__dirname, 'dist/assets'))) {
    copyDirSync(resolve(__dirname, 'dist/assets'), rootAssetsDir);
  }

  console.log('ResumeIQ Extension build complete!');
  console.log('Both directories are now 100% valid to load in Chrome:');
  console.log('  Option A (Root): ~/Downloads/AI _Resume_Builder/extension');
  console.log('  Option B (Dist): ~/Downloads/AI _Resume_Builder/extension/dist');
}

run().catch((err) => {
  console.error('Build failed:', err);
  process.exit(1);
});
