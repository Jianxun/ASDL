import React from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './app'
import { maybeStartDevHarness } from './devHarness'
import './styles.css'

maybeStartDevHarness()

const root = document.getElementById('root')
if (root) {
  createRoot(root).render(<App />)
}
