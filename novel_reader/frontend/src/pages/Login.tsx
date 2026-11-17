import { AppFooter } from '@/components/app/app-footer'
import { AppHeader } from '@/components/app/app-header'
import { LoginForm } from '@/components/app/login-form'

export default function Login() {
  return (
    <div className="flex min-h-svh flex-col">
      <AppHeader minimal />
      <main className="flex flex-1 items-center justify-center bg-[radial-gradient(circle_at_50%_0%,rgba(224,164,88,0.07),transparent_55%)] p-4">
        <LoginForm />
      </main>
      <AppFooter />
    </div>
  )
}
