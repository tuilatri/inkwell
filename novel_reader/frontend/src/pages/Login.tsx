import { useState, type FormEvent } from 'react'
import { apiFetch } from '../api/client'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    try {
      await apiFetch('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      })
      window.location.assign('/')
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'login failed')
    }
  }

  return (
    <main className="container">
      <h1>Inkwell Novel Reader</h1>
      <form className="card stack" onSubmit={submit}>
        <label>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="primary" type="submit">Log in</button>
      </form>
    </main>
  )
}
