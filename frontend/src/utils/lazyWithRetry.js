import { lazy } from 'react'

// After a deploy, Vite's content-hashed chunk filenames change. A tab left open
// from before the deploy will 404 on the old filename (Vercel's SPA catch-all
// then serves index.html, causing a MIME-type error) and crash the lazy-loaded
// tree since there's no error boundary. Reload once to pick up the fresh build.
export default function lazyWithRetry(componentImport) {
  return lazy(async () => {
    try {
      const component = await componentImport()
      sessionStorage.removeItem('chunk-load-refreshed')
      return component
    } catch (error) {
      const alreadyRefreshed = sessionStorage.getItem('chunk-load-refreshed') === '1'
      if (!alreadyRefreshed) {
        sessionStorage.setItem('chunk-load-refreshed', '1')
        window.location.reload()
        return new Promise(() => {}) // reloading — never resolve
      }
      sessionStorage.removeItem('chunk-load-refreshed')
      throw error
    }
  })
}
