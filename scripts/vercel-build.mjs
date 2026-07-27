/**
 * Vercel build: Vite SPA → public/, backend static CSS copied for invoice/feedback pages.
 * Flask API is deployed as a single Python serverless function (backend/app.py).
 */
import { execSync } from 'child_process'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.resolve(__dirname, '..')
const frontendDir = path.join(rootDir, 'frontend')
const publicDir = path.join(rootDir, 'public')

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true })
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name)
    const destPath = path.join(dest, entry.name)
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath)
    } else {
      fs.copyFileSync(srcPath, destPath)
    }
  }
}

console.log('[vercel-build] Building frontend (same-origin API on production web)...')
execSync('npm run build', {
  cwd: frontendDir,
  env: {
    ...process.env,
    VITE_API_BASE_URL: '',
    VITE_PUBLIC_BASE_URL: '',
  },
  stdio: 'inherit',
})

console.log('[vercel-build] Copying frontend/dist → public/')
fs.rmSync(publicDir, { recursive: true, force: true })
copyDir(path.join(frontendDir, 'dist'), publicDir)

const backendCss = path.join(rootDir, 'backend/static/css')
if (fs.existsSync(backendCss)) {
  console.log('[vercel-build] Copying backend/static/css → public/css/')
  copyDir(backendCss, path.join(publicDir, 'css'))
}

console.log('[vercel-build] Done.')
