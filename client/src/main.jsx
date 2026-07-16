import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { MsalProvider } from "@azure/msal-react"
import { msalInstance } from "./config/msal"
import { AuthProvider } from "./config/AuthContext"
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <MsalProvider instance={msalInstance}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MsalProvider>
  </StrictMode>,
)
