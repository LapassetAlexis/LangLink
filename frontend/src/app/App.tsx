import { useEffect, useState } from 'react'
import { Link, Navigate, Route, Routes, useNavigate } from 'react-router-dom'

import { ChatPage, DiscoverPage, InboxPage, WizardPage } from '../features/pages'
import { api, getToken, setToken } from '../lib/api'

function Wordmark() {
  return (
    <Link to="/" className="flex items-center gap-2.5 text-sm font-medium tracking-wide">
      <span
        aria-hidden="true"
        className="grid h-8 w-8 place-items-center rounded-full text-[13px] font-semibold text-[color:var(--ink-950)]"
        style={{ background: 'linear-gradient(160deg, var(--amber-400), var(--rose-400))' }}
      >
        L
      </span>
      <span className="text-[color:var(--sand-100)]">LangLink</span>
    </Link>
  )
}

const STEPS = [
  {
    n: '01',
    title: 'Dites qui vous êtes',
    body: "Votre langue, celle que vous apprenez, et trois passions minimum. Deux minutes, pas plus.",
  },
  {
    n: '02',
    title: 'Rencontrez la bonne personne',
    body: "Uniquement des gens dont la langue maternelle est celle que vous apprenez — et réciproquement.",
  },
  {
    n: '03',
    title: 'Écrivez sans pression',
    body: "Pas de présence, pas de « en train d'écrire ». Des messages, quand vous voulez, corrigés par un humain.",
  },
]

function Landing() {
  return (
    <div className="mx-auto max-w-6xl px-6 pb-20">
      <header className="flex items-center justify-between py-6">
        <Wordmark />
        <nav className="flex items-center gap-2">
          <Link className="btn-ghost hidden sm:inline-flex" to="/login">
            Se connecter
          </Link>
          <Link className="btn-primary" to="/signup">
            Commencer
          </Link>
        </nav>
      </header>

      <section className="grid items-center gap-12 py-16 lg:grid-cols-[1.1fr_0.9fr] lg:py-24">
        <div className="rise">
          <p className="eyebrow mb-5">Correspondance linguistique · sans IA</p>
          <h1 className="display text-5xl leading-[1.05] sm:text-6xl">
            Échangez avec des personnes qui apprennent votre langue.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-[color:var(--sand-300)]/80">
            Pas de chatbot, pas de leçons, pas de flamme à entretenir. Juste deux humains qui
            s&apos;apprennent mutuellement leur langue, autour de ce qui les passionne vraiment.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <Link className="btn-primary px-7 py-3.5" to="/signup">
              Créer mon profil
            </Link>
            <Link className="btn-ghost px-6 py-3.5" to="/login">
              J&apos;ai déjà un compte
            </Link>
          </div>
          <dl className="mt-12 flex flex-wrap gap-x-10 gap-y-4 border-t border-white/5 pt-6">
            {[
              ['Réciprocité', 'stricte, par construction'],
              ['0', 'message généré par IA'],
              ['Asynchrone', 'vous répondez quand vous voulez'],
            ].map(([value, label]) => (
              <div key={label}>
                <dt className="display text-xl">{value}</dt>
                <dd className="mt-0.5 text-xs text-white/45">{label}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="relative mx-auto w-full max-w-sm lg:mx-0">
          <div
            aria-hidden="true"
            className="absolute -inset-6 rounded-[2.5rem] opacity-60 blur-2xl"
            style={{
              background:
                'radial-gradient(60% 60% at 30% 20%, rgba(240,179,87,0.35), transparent 70%), radial-gradient(50% 50% at 80% 80%, rgba(111,211,192,0.28), transparent 70%)',
            }}
          />
          <article className="surface relative rotate-[-1.5deg] p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="display text-2xl">Yuki</p>
                <p className="mt-1 text-xs text-white/45">japonais → français · A2</p>
              </div>
              <span
                className="grid h-12 w-12 place-items-center rounded-full text-sm font-semibold"
                style={{
                  background: 'conic-gradient(var(--amber-400) 92%, rgba(255,255,255,0.08) 0)',
                }}
              >
                <span className="grid h-9 w-9 place-items-center rounded-full bg-[color:var(--ink-900)]">
                  92
                </span>
              </span>
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              {['🗡️ RPG', '🍜 Cuisine', '🚐 Road trips'].map((chip) => (
                <span key={chip} className="chip-on text-xs">
                  {chip}
                </span>
              ))}
            </div>
            <p className="mt-5 rounded-2xl bg-white/[0.03] px-4 py-3 text-sm leading-relaxed text-white/70">
              « J&apos;ai commencé le français avec des séries, et maintenant je rêve en
              français. C&apos;est grave ? »
            </p>
            <p className="mt-4 text-[11px] uppercase tracking-widest text-white/30">
              3 questions brise-glace prêtes
            </p>
          </article>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        {STEPS.map((step) => (
          <article key={step.n} className="surface p-6">
            <p className="text-xs font-medium tracking-[0.2em] text-[color:var(--amber-400)]">
              {step.n}
            </p>
            <h2 className="display mt-3 text-xl">{step.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-white/55">{step.body}</p>
          </article>
        ))}
      </section>

      <footer className="mt-16 flex flex-col items-start justify-between gap-3 border-t border-white/5 pt-6 text-xs text-white/35 sm:flex-row">
        <p>LangLink — échanges humains, outils déterministes.</p>
        <p>Aucune génération de texte automatique dans vos conversations.</p>
      </footer>
    </div>
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
      const result =
        mode === 'signup' ? await api.register(email, password) : await api.login(email, password)
      setToken(result.access_token)
      navigate('/onboarding')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Échec inattendu')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto grid min-h-screen max-w-6xl items-stretch gap-0 px-6 py-6 lg:grid-cols-2">
      <aside className="hidden flex-col justify-between rounded-l-[2rem] border border-white/5 border-r-0 bg-white/[0.02] p-10 lg:flex">
        <Wordmark />
        <div>
          <p className="display text-3xl leading-tight">
            « On n&apos;apprend pas une langue.
            <br />
            On apprend quelqu&apos;un. »
          </p>
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-white/45">
            Chaque échange est corrigé par la personne en face de vous — jamais par un modèle
            de langage.
          </p>
        </div>
        <p className="text-xs text-white/25">LangLink · {new Date().getFullYear()}</p>
      </aside>

      <main className="flex flex-col justify-center rounded-[2rem] border border-white/5 bg-[color:var(--ink-850)]/70 p-8 backdrop-blur sm:p-12 lg:rounded-l-none">
        <div className="mb-8 lg:hidden">
          <Wordmark />
        </div>
        <h1 className="display text-3xl">
          {mode === 'signup' ? 'Créer un compte' : 'Content de vous revoir'}
        </h1>
        <p className="mt-2 text-sm text-white/45">
          {mode === 'signup'
            ? 'Deux minutes, et vous rencontrez quelqu’un.'
            : 'Reprenez vos conversations là où vous les avez laissées.'}
        </p>

        <form className="mt-8 flex flex-col gap-4" onSubmit={submit}>
          <label className="flex flex-col gap-1.5 text-sm text-white/60">
            Adresse email
            <input
              className="field"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1.5 text-sm text-white/60">
            Mot de passe
            <input
              className="field"
              type="password"
              autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
              required
              minLength={10}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            {mode === 'signup' && (
              <span className="text-xs text-white/30">10 caractères minimum.</span>
            )}
          </label>

          {error && (
            <p role="alert" className="rounded-2xl bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </p>
          )}

          <button className="btn-primary mt-2 py-3.5" type="submit" disabled={busy}>
            {busy ? 'Un instant…' : mode === 'signup' ? 'Créer mon compte' : 'Entrer'}
          </button>
        </form>

        <button
          className="mt-6 text-sm text-white/40 underline-offset-4 hover:text-white/70 hover:underline"
          onClick={() => navigate(mode === 'signup' ? '/login' : '/signup')}
        >
          {mode === 'signup' ? "J'ai déjà un compte" : 'Créer un compte'}
        </button>
      </main>
    </div>
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

  if (!ready) return <p className="p-8 text-white/40">Chargement…</p>

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
