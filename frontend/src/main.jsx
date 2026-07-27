import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import './styles/components.css'
import './styles/page-layouts.css'

// Keep --vh in sync with the actual visible viewport, so 100vh-style layouts
// shrink correctly when the mobile/tablet on-screen keyboard opens.
// iOS Safari and some Android browsers don't shrink window.innerHeight; visualViewport does.
const setAppVh = () => {
  const h = (window.visualViewport && window.visualViewport.height) || window.innerHeight
  document.documentElement.style.setProperty('--vh', `${h * 0.01}px`)
  document.documentElement.style.setProperty('--app-height', `${h}px`)
}
setAppVh()
window.addEventListener('resize', setAppVh)
window.addEventListener('orientationchange', setAppVh)
if (window.visualViewport) {
  window.visualViewport.addEventListener('resize', setAppVh)
  window.visualViewport.addEventListener('scroll', setAppVh)
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

