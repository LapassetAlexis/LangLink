import { useEffect, useState } from 'react'
import { Link, Navigate, Route, Routes, useNavigate } from 'react-router-dom'

import { ChatPage, DiscoverPage, InboxPage, WizardPage } from '../features/pages'
import { api, getToken, setToken } from '../lib/api'

function Landing() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-6 px-6 py-16">
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-brand-400">LangLink</p>
      <h1 className="text-4xl font-semibold leading-tight sm:text-5xl">
        Échangez avec des personnes qui apprennent votre langue.
      </h1>
      <p className="max-w-xl text-lg text-slate-400">
        Correspondance asynchrone autour d&apos;intérêts communs. Pas de chatbot, pas de
        pression : des humains, des corrections bienveillantes, des outils pour comprendre.
      </p>
      <div className="flex gap-3">
        <Link className="rounded-lg bg-brand-600 px-5 py-3 font-medium hover:bg-brand-700" to="/signup">
          Créer un compte
        </Link>
        <Link className="rounded-lg border border-slate-700 px-5 py-3 hover:border-slate-500" to="/login">
          Se connecter
        </Link>
      </div>
    </main>
  )
}

function AuthPage({ mode }: { mode: 'login' | 'signup' }) {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const result = mode === 'signup' ? await api.register(email, password) : await api.login(email, password)
      setToken(result.access_token)
      navigate('/onboarding')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Échec inattendu')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 px-6">
      <h1 className="text-2xl font-semibold">{mode === 'signup' ? 'Créer un compte' : 'Se connecter'}</h1>
      <form className="flex flex-col gap-4" onSubmit={submit}>
        <label className="flex flex-col gap-1 text-sm text-slate-300">
          Email
          <input
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-slate-300">
          Mot de passe
          <input
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
            type="password"
            required
            minLength={10}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {error && (
          <p role="alert" className="rounded-lg bg-red-950 px-3 py-2 text-sm text-red-300">
            {error}
          </p>
        )}
        <button
          className="rounded-lg bg-brand-600 px-4 py-3 font-medium disabled:opacity-50"
          type="submit"
          disabled={busy}
        >
          {busy ? 'Un instant…' : mode === 'signup' ? 'Créer mon compte' : 'Entrer'}
        </button>
      </form>
      <button
        className="text-sm text-slate-400 underline"
        onClick={() => navigate(mode === 'signup' ? '/login' : '/signup')}
      >
        {mode === 'signup' ? "J'ai déjà un compte" : 'Créer un compte'}
      </button>
    </main>
  )
}

function Guard({ children }: { children: React.ReactNode }) {
  if (!getToken()) return <Navigate to="/login" replace />
  return <>{children}</>
}

export function App() {
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (!getToken()) {
      setReady(true)
      return
    }
    api
      .me()
      .catch(() => setToken(null))
      .finally(() => setReady(true))
  }, [])

  if (!ready) return <p className="p-8 text-slate-400">Chargement…</p>

  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/signup" element={<AuthPage mode="signup" />} />
      <Route
        path="/onboarding"
        element={
          <Guard>
            <WizardPage />
          </Guard>
        }
      />
      <Route
        path="/discover"
        element={
          <Guard>
            <DiscoverPage />
          </Guard>
        }
      />
      <Route
        path="/messages"
        element={
          <Guard>
            <InboxPage />
          </Guard>
        }
      />
      <Route
        path="/messages/:matchId"
        element={
          <Guard>
            <ChatPage />
          </Guard>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
