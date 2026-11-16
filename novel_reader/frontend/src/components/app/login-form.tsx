import { useState, type FormEvent } from 'react'
import { apiFetch } from '@/api/client'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Spinner } from '@/components/ui/spinner'

export function LoginForm() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setPending(true)
    try {
      await apiFetch('/api/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })
      window.location.assign('/')
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Đăng nhập thất bại')
      setPending(false)
    }
  }

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle className="text-2xl">Inkwell Novel Reader</CardTitle>
        <CardDescription>Đăng nhập để tiếp tục đọc truyện của bạn.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={submit}>
          <div className="space-y-2">
            <Label htmlFor="username">Tên đăng nhập</Label>
            <Input id="username" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Mật khẩu</Label>
            <Input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <Alert variant="destructive">{error}</Alert>}
          <Button className="w-full" type="submit" disabled={pending}>
            {pending ? <Spinner label="Đang đăng nhập…" /> : 'Đăng nhập'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
