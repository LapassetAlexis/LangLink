import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import {
  api,
  ApiError,
  type Candidate,
  type Conversation,
  type InterestGroup,
  type MatchDetail,
  type Message,
  type OnboardingState,
} from '../lib/api'

import { LanguagePair } from '../components/LanguagePair'
import { LANGUAGES } from '../lib/languages'

const LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.problem.detail ?? error.problem.title
  return error instanceof Error ? error.message : 'Erreur inattendue'
}

/* ------------------------------------------------------------------ wizard */

export function WizardPage() {
  const navigate = useNavigate()
  const [state, setState] = useState<OnboardingState | null>(null)
  const [catalog, setCatalog] = useState<InterestGroup[]>([])
  const [native, setNative] = useState('fr')
  const [target, setTarget] = useState('ja')
  const [level, setLevel] = useState('A2')
  const [selected, setSelected] = useState<number[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    void Promise.all([api.onboardingState(), api.interests()])
      .then(([current, groups]) => {
        setState(current)
        setCatalog(groups)
        setNative(current.native_language ?? 'fr')
        setTarget(current.target_language ?? 'ja')
        setLevel(current.target_level ?? 'A2')
        setSelected(current.interest_ids)
      })
      .catch((err) => setError(errorMessage(err)))
  }, [])

  const step = state?.step ?? 1

  async function saveLanguages() {
    setBusy(true)
    setError(null)
    try {
      setState(await api.setLanguages(native, target, level))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function saveInterests() {
    setBusy(true)
    setError(null)
    try {
      setState(await api.setInterests(selected))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function finish() {
    setBusy(true)
    setError(null)
    try {
      await api.complete()
      navigate('/discover')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  function toggle(id: number) {
    setSelected((current) =>
      current.includes(id) ? current.filter((value) => value !== id) : [...current, id].slice(0, 12),
    )
  }

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-10">
      <header className="flex items-center gap-2" aria-label={`Étape ${step} sur 3`}>
        {[1, 2, 3].map((index) => (
          <span
            key={index}
            aria-current={index === step ? 'step' : undefined}
            className={`h-2 flex-1 rounded-full ${index <= step ? 'bg-brand-500' : 'bg-slate-800'}`}
          />
        ))}
        <span className="ml-2 text-xs text-slate-400">{step}/3</span>
      </header>

      {error && (
        <p role="alert" className="rounded-lg bg-red-950 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {step === 1 && (
        <section className="flex flex-col gap-4">
          <h1 className="text-2xl font-semibold">Quelles langues échangez-vous ?</h1>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-1 text-sm text-slate-300">
              Ma langue maternelle
              <select
                className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                value={native}
                onChange={(event) => setNative(event.target.value)}
              >
                {LANGUAGES.map((language) => (
                  <option key={language.code} value={language.code}>
                    {language.flag} {language.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-sm text-slate-300">
              Langue que j&apos;apprends
              <select
                className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                value={target}
                onChange={(event) => setTarget(event.target.value)}
              >
                {LANGUAGES.map((language) => (
                  <option key={language.code} value={language.code}>
                    {language.flag} {language.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="flex flex-wrap gap-2">
            {LEVELS.map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setLevel(value)}
                className={`rounded-lg px-4 py-2 text-sm ${
                  value === level ? 'bg-brand-600' : 'border border-slate-700 hover:border-slate-500'
                }`}
              >
                {value}
              </button>
            ))}
          </div>
          <p className="text-sm text-slate-400">
            {native === target
              ? 'Choisissez deux langues différentes.'
              : `Vous apprendrez le ${target} · votre correspondant apprendra le ${native}.`}
          </p>
          <button
            className="self-start rounded-lg bg-brand-600 px-5 py-3 font-medium disabled:opacity-40"
            disabled={native === target || busy}
            onClick={saveLanguages}
          >
            Continuer
          </button>
        </section>
      )}

      {step === 2 && (
        <section className="flex flex-col gap-4">
          <h1 className="text-2xl font-semibold">Vos centres d&apos;intérêt</h1>
          <p className="text-sm text-slate-400">
            {selected.length}/12 — minimum 3 pour rencontrer quelqu&apos;un.
          </p>
          {catalog.map((group) => (
            <div key={group.category} className="flex flex-col gap-2">
              <h2 className="text-sm font-medium uppercase tracking-wide text-slate-400">
                {group.category}
              </h2>
              <div className="flex flex-wrap gap-2">
                {group.interests.map((interest) => {
                  const active = selected.includes(interest.id)
                  return (
                    <button
                      key={interest.id}
                      type="button"
                      aria-pressed={active}
                      onClick={() => toggle(interest.id)}
                      className={`rounded-full border px-3 py-1.5 text-sm ${
                        active
                          ? 'border-brand-500 bg-brand-600/20 text-brand-200'
                          : 'border-slate-700 text-slate-300 hover:border-slate-500'
                      }`}
                    >
                      <span aria-hidden="true">{interest.emoji}</span> {interest.label}
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
          <div className="flex gap-3">
            <button
              className="rounded-lg border border-slate-700 px-4 py-2"
              onClick={() => void saveLanguages()}
            >
              Retour
            </button>
            <button
              className="rounded-lg bg-brand-600 px-5 py-2 font-medium disabled:opacity-40"
              disabled={selected.length < 3 || busy}
              onClick={saveInterests}
            >
              Continuer
            </button>
          </div>
        </section>
      )}

      {step === 3 && (
        <section className="flex flex-col gap-4">
          <h1 className="text-2xl font-semibold">Dernière touche</h1>
          <p className="text-slate-400">
            Votre profil est prêt. Vous pouvez ajouter une photo plus tard depuis vos réglages.
          </p>
          <div className="flex gap-3">
            <button className="rounded-lg bg-brand-600 px-5 py-3 font-medium" onClick={finish}>
              Découvrir des profils
            </button>
            <button
              className="rounded-lg border border-slate-700 px-5 py-3"
              onClick={() => navigate('/discover')}
            >
              Plus tard
            </button>
          </div>
        </section>
      )}
    </main>
  )
}

/* --------------------------------------------------------------- discovery */

export function DiscoverPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [index, setIndex] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [match, setMatch] = useState<string | null>(null)
  const [exhausted, setExhausted] = useState(false)

  useEffect(() => {
    api
      .feed()
      .then((feed) => {
        setCandidates(feed.items)
        setExhausted(feed.items.length === 0)
      })
      .catch((err) => setError(errorMessage(err)))
  }, [])

  const current = candidates[index]

  async function decide(direction: 'like' | 'pass') {
    if (!current) return
    try {
      const result = await api.swipe(current.user_id, direction)
      if (result.match) setMatch(current.display_name)
      const next = index + 1
      setIndex(next)
      if (next >= candidates.length) setExhausted(true)
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === 'ArrowRight') void decide('like')
      if (event.key === 'ArrowLeft') void decide('pass')
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  if (error) return <p className="p-8 text-red-300">{error}</p>

  if (exhausted || !current)
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6 text-center">
        <h1 className="text-2xl font-semibold">Plus de profils pour aujourd&apos;hui</h1>
        <p className="text-slate-400">Revenez demain, ou allez voir vos conversations.</p>
        <Link className="rounded-lg bg-brand-600 px-5 py-3" to="/messages">
          Mes messages
        </Link>
      </main>
    )

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6 py-10">
      <article className="surface flex flex-col gap-4 p-7">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="display text-3xl">{current.display_name}</h1>
            <p className="mt-1.5 text-sm text-white/45">
              <LanguagePair
                native={current.native_language}
                target={current.target_language}
                className="text-white/70"
              />{' '}
              · niveau {current.target_level}
            </p>
          </div>
          <span
            className="grid h-14 w-14 shrink-0 place-items-center rounded-full"
            style={{
              background: `conic-gradient(var(--amber-400) ${current.score}%, rgba(255,255,255,0.07) 0)`,
            }}
            aria-label={`Affinité ${current.score} sur 100`}
          >
            <span className="grid h-11 w-11 place-items-center rounded-full bg-[color:var(--ink-900)] text-sm font-semibold">
              {current.score}
            </span>
          </span>
        </div>
        {current.bio && <p className="text-sm leading-relaxed text-white/65">{current.bio}</p>}
        <div className="flex flex-wrap gap-2 pt-1">
          <span className="chip-on text-xs">
            {current.common_interest_ids.length} intérêts en commun
          </span>
          {current.birth_year && (
            <span className="chip text-xs">{new Date().getFullYear() - current.birth_year} ans</span>
          )}
        </div>
      </article>
      <div className="flex gap-3">
        <button className="btn-ghost flex-1 py-3.5" onClick={() => void decide('pass')}>
          Passer
        </button>
        <button className="btn-primary flex-1 py-3.5" onClick={() => void decide('like')}>
          J&apos;aime
        </button>
      </div>
      <p className="text-center text-xs text-slate-500">← passer · → aimer</p>
      {match && (
        <div role="status" className="rounded-lg bg-emerald-950 px-4 py-3 text-emerald-200">
          C&apos;est un match avec {match} !{' '}
          <Link className="underline" to="/messages">
            Envoyer un message
          </Link>
        </div>
      )}
    </main>
  )
}

/* ------------------------------------------------------------------ inbox */

export function InboxPage() {
  const [items, setItems] = useState<Conversation[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .conversations()
      .then((data) => setItems(data.items))
      .catch((err) => setError(errorMessage(err)))
  }, [])

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-4 px-6 py-10">
      <h1 className="text-2xl font-semibold">Conversations</h1>
      {error && <p className="text-red-300">{error}</p>}
      {items.length === 0 && <p className="text-slate-400">Aucun match pour le moment.</p>}
      <ul className="flex flex-col gap-2">
        {items.map((conversation) => (
          <li key={conversation.id}>
            <Link
              className="flex items-center justify-between rounded-2xl border border-white/5 bg-white/[0.02] px-5 py-4 transition hover:border-white/20 hover:bg-white/[0.04]"
              to={`/messages/${conversation.id}`}
            >
              <span>
                <span className="font-medium">{conversation.display_name}</span>
                <span className="ml-2 text-xs text-white/45"><LanguagePair pair={conversation.languages} /></span>
                <span className="block text-sm text-slate-400">
                  {conversation.last_message ?? 'Nouveau match — dites bonjour'}
                </span>
              </span>
              {conversation.unread_count > 0 && (
                <span className="rounded-full bg-brand-600 px-2 py-0.5 text-xs">
                  {conversation.unread_count}
                </span>
              )}
            </Link>
          </li>
        ))}
      </ul>
      <Link className="text-sm text-slate-400 underline" to="/discover">
        Découvrir des profils
      </Link>
    </main>
  )
}

/* ------------------------------------------------------------------- chat */

export function ChatPage() {
  const { matchId = '' } = useParams()
  const [detail, setDetail] = useState<MatchDetail | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [draft, setDraft] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [translations, setTranslations] = useState<Record<string, string>>({})
  const [reading, setReading] = useState<Record<string, Array<{ surface: string; romaji: string }>>>({})
  const [pendingCorrection, setPendingCorrection] = useState<{ message: Message; start: number; end: number } | null>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const mine = useMemo(() => messages, [messages])

  useEffect(() => {
    void Promise.all([api.match(matchId), api.messages(matchId)])
      .then(([matchDetail, page]) => {
        setDetail(matchDetail)
        setMessages([...page.items].reverse())
      })
      .catch((err) => setError(errorMessage(err)))
  }, [matchId])

  useEffect(() => {
    const last = messages.at(-1)
    if (last && detail?.other) void api.markRead(matchId, last.id).catch(() => undefined)
  }, [messages, matchId, detail])

  async function send() {
    const body = draft.trim()
    if (!body) return
    setDraft('')
    try {
      const created = await api.send(matchId, body, crypto.randomUUID())
      setMessages((current) => [
        ...current,
        {
          id: created.id,
          sender_id: 'me',
          body: created.body,
          body_rendered: created.body,
          body_lang: null,
          created_at: new Date().toISOString(),
          edited_at: null,
          deleted_at: null,
          corrections: [],
        },
      ])
    } catch (err) {
      setDraft(body)
      setError(errorMessage(err))
    }
  }

  async function translate(message: Message) {
    try {
      const result = await api.translate(message.id)
      setTranslations((current) => ({ ...current, [message.id]: `${result.translated} (${result.provider})` }))
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  async function showFurigana(message: Message) {
    try {
      const result = await api.readingAid(message.id)
      setReading((current) => ({ ...current, [message.id]: result.tokens }))
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  function startCorrection(message: Message) {
    const selection = window.getSelection()
    if (!selection || selection.isCollapsed) return
    const container = selection.anchorNode
    if (!container || !(container.parentElement?.dataset.messageId === message.id)) return
    const start = selection.anchorOffset
    const end = selection.focusOffset
    if (start === end) return
    setPendingCorrection({ message, start: Math.min(start, end), end: Math.max(start, end) })
  }

  async function submitCorrection(replacement: string) {
    if (!pendingCorrection) return
    try {
      await api.correct(pendingCorrection.message.id, {
        start_offset: pendingCorrection.start,
        end_offset: pendingCorrection.end,
        replacement,
      })
      setPendingCorrection(null)
      const page = await api.messages(matchId)
      setMessages([...page.items].reverse())
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  if (error && !detail) return <p className="p-8 text-red-300">{error}</p>
  if (!detail) return <p className="p-8 text-slate-400">Chargement…</p>

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col px-6 py-6">
      <header className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">{detail.other?.display_name}</h1>
          <p className="text-xs text-slate-500">
            <LanguagePair
              native={detail.other?.native_language}
              target={detail.other?.target_language}
            />{' '}
            · affinité {detail.affinity_score}/100
          </p>
        </div>
        <Link className="text-sm text-slate-400 underline" to="/messages">
          Retour
        </Link>
      </header>

      {detail.icebreakers.length > 0 && (
        <aside className="mb-4 rounded-xl border border-slate-800 p-3">
          <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Brise-glace</p>
          <ul className="flex flex-col gap-2">
            {detail.icebreakers.map((ice) => (
              <li key={ice.position}>
                <button
                  className="text-left text-sm text-brand-300 hover:underline"
                  onClick={() => setDraft((current) => (current ? `${current} ${ice.question_fr}` : ice.question_fr))}
                >
                  {ice.question_fr}
                </button>
              </li>
            ))}
          </ul>
        </aside>
      )}

      <div ref={listRef} className="flex flex-1 flex-col gap-3 overflow-y-auto">
        {mine.map((message) => (
          <article
            key={message.id}
            data-message-id={message.id}
            onMouseUp={() => startCorrection(message)}
            className="bubble-them rise"
          >
            <p className="whitespace-pre-wrap text-slate-100">
              {reading[message.id]
                ? (reading[message.id] ?? []).map((token, position) => (
                    <ruby key={position}>
                      {token.surface}
                      <rt className="text-xs text-slate-400">{token.romaji}</rt>
                    </ruby>
                  ))
                : message.body_rendered}
            </p>
            {translations[message.id] && (
              <p className="mt-2 border-l-2 border-brand-700 pl-2 text-sm text-slate-400">
                {translations[message.id]}
              </p>
            )}
            <div className="mt-2 flex gap-3 text-xs text-slate-500">
              <button className="hover:underline" onClick={() => void translate(message)}>
                Traduire
              </button>
              <button className="hover:underline" onClick={() => void showFurigana(message)}>
                Furigana
              </button>
              <span>{new Date(message.created_at).toLocaleString('fr-FR')}</span>
            </div>
            {message.corrections
              .filter((correction) => correction.status === 'pending')
              .map((correction) => (
                <div key={correction.id} className="mt-2 rounded-lg bg-amber-950/40 p-2 text-sm">
                  <p className="text-amber-200">
                    « {correction.original_text} » → « {correction.replacement} »
                  </p>
                  <div className="mt-1 flex gap-2">
                    <button
                      className="rounded bg-emerald-700 px-2 py-1 text-xs"
                      onClick={() => void api.acceptCorrection(correction.id).then(() => api.messages(matchId)).then((page) => setMessages([...page.items].reverse()))}
                    >
                      Accepter
                    </button>
                    <button
                      className="rounded border border-slate-700 px-2 py-1 text-xs"
                      onClick={() => void api.rejectCorrection(correction.id)}
                    >
                      Refuser
                    </button>
                  </div>
                </div>
              ))}
          </article>
        ))}
      </div>

      {pendingCorrection && (
        <form
          className="mt-3 rounded-xl border border-amber-800 p-3"
          onSubmit={(event) => {
            event.preventDefault()
            const data = new FormData(event.currentTarget)
            void submitCorrection(String(data.get('replacement') ?? ''))
          }}
        >
          <p className="text-sm text-amber-200">
            Corriger « {pendingCorrection.message.body_rendered.slice(pendingCorrection.start, pendingCorrection.end)} »
          </p>
          <input
            name="replacement"
            required
            className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
            placeholder="Votre correction"
          />
          <div className="mt-2 flex gap-2">
            <button className="rounded bg-brand-600 px-3 py-1.5 text-sm" type="submit">
              Suggérer
            </button>
            <button
              className="rounded border border-slate-700 px-3 py-1.5 text-sm"
              type="button"
              onClick={() => setPendingCorrection(null)}
            >
              Annuler
            </button>
          </div>
        </form>
      )}

      {error && <p className="mt-2 text-sm text-red-300">{error}</p>}

      <form
        className="mt-4 flex gap-2"
        onSubmit={(event) => {
          event.preventDefault()
          void send()
        }}
      >
        <input
          className="field flex-1"
          placeholder="Écrire un message…"
          maxLength={4000}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
        />
        <button className="btn-primary px-5" type="submit">
          Envoyer
        </button>
      </form>
    </main>
  )
}
