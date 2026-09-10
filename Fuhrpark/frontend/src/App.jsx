import { useEffect, useState } from 'react'

const API_BASE_URL = 'http://localhost:8000'

function App() {
  const [status, setStatus] = useState('Lade API-Status...')

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then((r) => r.json())
      .then((d) => setStatus(`API Status: ${d.status}`))
      .catch(() => setStatus('API nicht erreichbar'))
  }, [])

  return (
    <main className="container">
      <h1>Fuhrpark</h1>
      <p>Projekt gestartet ✅</p>
      <p>{status}</p>
    </main>
  )
}

export default App
