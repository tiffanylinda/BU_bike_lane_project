import React from 'react'
import ReactDOM from 'react-dom/client'
import RiderApp from './RiderApp.jsx'
import './styles.css'

// Entry point for the rider web app (rider.html). Same styles as the replay demo.
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RiderApp />
  </React.StrictMode>,
)
