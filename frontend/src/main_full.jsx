import React from 'react'
import { createRoot } from 'react-dom/client'
import AppFull from './AppFull'
import './styles.css'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppFull />
  </React.StrictMode>
)
