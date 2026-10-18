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
import { defaultTimezoneOf, labelOf, LANGUAGES } from '../lib/languages'
import { levelLabel, levelOptions, levelTooltip } from '../lib/levels'


function relativeDate(iso: string | null): string {
  if (!iso) return ''
  const then = new Date(iso).getTime()
  const minutes = Math.round((Date.now() - then) / 60000)
  if (minutes < 1) return "à l'instant"
  if (minutes < 60) return `il y a ${minutes} min`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `il y a ${hours} h`
  const days = Math.round(hours / 24)
  if (days === 1) return 'hier'
  if (days < 7) return `il y a ${days} jours`
  return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
}

function localClock(timezone: string | null | undefined): { time: string; hour: number } | null {
  if (!timezone) return null
  try {
    const now = new Date()
    const time = new Intl.DateTimeFormat('fr-FR', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: timezone,
    }).format(now)
    const hour = Number(
      new Intl.DateTimeFormat('en-GB', { hour: '2-digit', hour12: false, timeZone: timezone }).format(
        now,
      ),
    )
    return { time, hour }
  } catch {
    return null
  }
}

const STATUS_LABEL: Record<string, string> = {
  active: '',
  unmatched: 'conversation fermée',
  blocked: 'profil bloqué',
}

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
                    {language.label}
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
                    {language.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="flex flex-wrap gap-2">
            {levelOptions(target).map((option) => (
              <button
                key={option.code}
                type="button"
                title={levelTooltip(option.code, target)}
                onClick={() => setLevel(option.code)}
                className={option.code === level ? 'btn-primary px-4 py-2' : 'btn-ghost px-4 py-2'}
              >
                {option.label}
              </button>
            ))}
          </div>
          <p className="text-sm text-slate-400">
            {native === target
              ? 'Choisissez deux langues différentes.'
              : `Vous apprendrez le ${labelOf(target).toLowerCase()} · votre correspondant apprendra le ${labelOf(native).toLowerCase()}.`}
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
              · <span title={levelTooltip(current.target_level)}>
                niveau {levelLabel(current.target_level, current.target_language)}
              </span>
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
    <div className="mx-auto grid max-w-5xl gap-8 px-5 py-8 lg:grid-cols-[minmax(0,420px)_1fr]">
      <section>
        <header className="mb-5 flex items-baseline justify-between">
          <h1 className="display text-2xl">Conversations</h1>
          <span className="text-xs text-white/35">
            {items.length} {items.length > 1 ? 'fils' : 'fil'}
          </span>
        </header>

        {error && (
          <p role="alert" className="rounded-2xl bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </p>
        )}

        {items.length === 0 ? (
          <div className="surface flex flex-col items-start gap-3 p-6">
            <p className="display text-lg">Aucune conversation</p>
            <p className="text-sm leading-relaxed text-white/50">
              Les conversations s&apos;ouvrent quand deux personnes se plaisent mutuellement.
              Commence par parcourir quelques profils.
            </p>
            <Link className="btn-primary mt-1" to="/discover">
              Découvrir des profils
            </Link>
          </div>
        ) : (
          <ul className="flex flex-col gap-2">
            {items.map((conversation) => (
              <li key={conversation.id}>
                <Link
                  className="group flex items-center gap-3.5 rounded-2xl border border-white/[0.06] bg-white/[0.02] px-4 py-3.5 transition hover:border-white/20 hover:bg-white/[0.05]"
                  to={`/messages/${conversation.id}`}
                >
                  <span
                    aria-hidden="true"
                    className="grid h-11 w-11 shrink-0 place-items-center rounded-full text-sm font-semibold text-[color:var(--ink-950)]"
                    style={{
                      background: 'linear-gradient(150deg, var(--amber-400), var(--rose-400))',
                    }}
                  >
                    {conversation.display_name.slice(0, 1).toUpperCase()}
                  </span>

                  <span className="min-w-0 flex-1">
                    <span className="flex items-baseline justify-between gap-2">
                      <span className="truncate font-medium">{conversation.display_name}</span>
                      {conversation.last_message_at && (
                        <time
                          className="shrink-0 text-[11px] text-white/30"
                          dateTime={conversation.last_message_at}
                          title={new Date(conversation.last_message_at).toLocaleString('fr-FR')}
                        >
                          {relativeDate(conversation.last_message_at)}
                        </time>
                      )}
                    </span>
                    <span className="mt-0.5 block truncate text-sm text-white/45 group-hover:text-white/60">
                      {conversation.last_message ?? 'Nouveau match — dites bonjour'}
                    </span>
                    <span className="mt-1 flex items-center gap-2 text-[11px] text-white/30">
                      <LanguagePair pair={conversation.languages} />
                      {conversation.status !== 'active' && (
                        <span className="text-amber-300/80">
                          · {STATUS_LABEL[conversation.status] ?? conversation.status}
                        </span>
                      )}
                    </span>
                  </span>

                  {conversation.unread_count > 0 && conversation.status === 'active' && (
                    <span className="shrink-0 rounded-full bg-brand-500 px-2 py-0.5 text-[11px] font-semibold text-[color:var(--ink-950)]">
                      {conversation.unread_count}
                    </span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <aside className="hidden lg:block">
        <div
          className="relative overflow-hidden rounded-3xl border border-white/[0.06] p-8"
          style={{
            background:
              'radial-gradient(120% 90% at 15% 0%, rgba(240,179,87,0.14), transparent 60%), radial-gradient(90% 80% at 90% 100%, rgba(111,211,192,0.12), transparent 55%), var(--ink-850)',
          }}
        >
          <p className="eyebrow">Correspondance</p>
          <p className="display mt-3 text-2xl leading-snug">
            Chaque message est corrigé par une personne, jamais par une machine.
          </p>
          <ul className="mt-6 flex flex-col gap-3 text-sm text-white/55">
            <li className="flex gap-3">
              <span aria-hidden="true" className="text-brand-400">
                ✳
              </span>
              Sélectionne un fil pour reprendre la discussion.
            </li>
            <li className="flex gap-3">
              <span aria-hidden="true" className="text-brand-400">
                ✳
              </span>
              L&apos;heure affichée est celle de ton correspondant.
            </li>
            <li className="flex gap-3">
              <span aria-hidden="true" className="text-brand-400">
                ✳
              </span>
              Survole un mot pour en demander le sens.
            </li>
          </ul>
        </div>
      </aside>
    </div>
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
  const [iceTranslations, setIceTranslations] = useState<Record<number, string>>({})
  const [wordTokens, setWordTokens] = useState<Record<string, string[]>>({})
  const [lexPanel, setLexPanel] = useState<{
    word: string
    source: string
    senses: Array<{ part_of_speech: string; definition: string }>
    reading: { kana: string; romaji: string } | null
  } | null>(null)
  const [lexBusy, setLexBusy] = useState(false)
  const [greeting, setGreeting] = useState<string | null>(null)
  const [iceBusy, setIceBusy] = useState<number | null>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const mine = useMemo(() => messages, [messages])

  // premiere langue du correspondant : les questions sont traduites dès l'ouverture.
  useEffect(() => {
    const other = detail?.other
    if (!other || other.native_language === 'fr') return
    let cancelled = false
    void Promise.all(
      detail.icebreakers.map(async (ice) => {
        try {
          const result = await api.translateText(ice.question_fr, 'fr', other.native_language)
          return [ice.position, result.translated] as const
        } catch {
          return null
        }
      }),
    ).then((pairs) => {
      if (cancelled) return
      const next: Record<number, string> = {}
      for (const pair of pairs) {
        if (pair) next[pair[0]] = pair[1]
      }
      setIceTranslations((current) => ({ ...next, ...current }))
    })
    return () => {
      cancelled = true
    }
  }, [detail?.id, detail?.other?.native_language])

  useEffect(() => {
    void Promise.all([api.match(matchId), api.messages(matchId)])
      .then(([matchDetail, page]) => {
        setDetail(matchDetail)
        setMessages([...page.items].reverse())
      })
      .catch((err) => setError(errorMessage(err)))
  }, [matchId])

  const today = new Date().toDateString()
  const alreadyToday = messages.some((m) => new Date(m.created_at).toDateString() === today)

  // Salutation du jour : proposée, jamais envoyée seule (REQ-ICE-05).
  useEffect(() => {
    const other = detail?.other
    if (!other || alreadyToday) {
      setGreeting(null)
      return
    }
    const theirClock = localClock(other.timezone ?? defaultTimezoneOf(other.native_language))
    const hour = theirClock?.hour ?? new Date().getHours()
    const french = hour < 18 ? 'Bonjour' : 'Bonsoir'
    if (other.native_language === 'fr') {
      setGreeting(french)
      return
    }
    let cancelled = false
    api
      .translateText(french, 'fr', other.native_language)
      .then((result) => {
        if (!cancelled) setGreeting(result.translated)
      })
      .catch(() => {
        if (!cancelled) setGreeting(french)
      })
    return () => {
      cancelled = true
    }
  }, [detail?.id, detail?.other?.native_language, alreadyToday])

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

  async function toggleWordMode(message: Message) {
    if (wordTokens[message.id]) {
      setWordTokens((current) => {
        const next = { ...current }
        delete next[message.id]
        return next
      })
      return
    }
    const lang = detail?.other?.native_language ?? 'en'
    try {
      let tokens: string[]
      if (lang === 'ja') {
        const known = reading[message.id]
        const fetched = known ?? (await api.readingAid(message.id)).tokens
        if (!known) setReading((current) => ({ ...current, [message.id]: fetched }))
        tokens = fetched.map((token) => token.surface)
      } else {
        tokens = message.body_rendered.split(/(\s+)/)
      }
      setWordTokens((current) => ({ ...current, [message.id]: tokens }))
    } catch {
      setError('Segmentation indisponible pour ce message.')
    }
  }

  async function lookUp(raw: string) {
    const word = raw.replace(/[.,!?;:«»"()\u3002\uff01\uff1f]/g, '').trim()
    if (!word) return
    setLexBusy(true)
    try {
      const lang = detail?.other?.native_language ?? 'en'
      setLexPanel(await api.lexicon(word, lang))
    } catch {
      setError('Aide indisponible pour ce mot.')
    } finally {
      setLexBusy(false)
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
            · niveau {levelLabel(detail.other?.target_level, detail.other?.target_language)} ·
            affinité {detail.affinity_score}/100
            {(() => {
              const clock = localClock(
                detail.other?.timezone ?? defaultTimezoneOf(detail.other?.native_language),
              )
              return clock ? (
                <span className="block text-[11px] text-white/35">
                  il est {clock.time} chez {detail.other?.display_name}
                  {` (${detail.other?.timezone ?? defaultTimezoneOf(detail.other?.native_language) ?? '?'})`}
                </span>
              ) : null
            })()}
          </p>
        </div>
        <Link className="text-sm text-slate-400 underline" to="/messages">
          Retour
        </Link>
      </header>

      {greeting && !alreadyToday && (
        <aside className="mb-3 flex items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
          <div>
            <p className="text-[11px] uppercase tracking-widest text-white/35">
              Pour commencer la journée
            </p>
            <p className="mt-0.5 text-sm text-white/80">{greeting}</p>
          </div>
          <button className="btn-ghost px-4 py-2 text-xs" onClick={() => setDraft(greeting)}>
            Utiliser
          </button>
        </aside>
      )}

      {detail.icebreakers.length > 0 && (
        <aside className="mb-4 rounded-xl border border-slate-800 p-3">
          <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Brise-glace</p>
          <ul className="flex flex-col gap-2">
            {detail.icebreakers.map((ice) => {
              const translated = iceTranslations[ice.position]
              const shown = translated ?? ice.question_fr
              return (
                <li key={ice.position} className="flex flex-col gap-1">
                  <span className="text-sm text-white/80">{shown}</span>
                  <span className="flex gap-3 text-[11px] text-white/35">
                    <button
                      className="hover:text-white/70"
                      onClick={() =>
                        setDraft((current) => (current ? `${current} ${shown}` : shown))
                      }
                    >
                      Utiliser
                    </button>
                    {detail.other?.native_language && (
                      <button
                        className="hover:text-white/70 disabled:opacity-40"
                        disabled={iceBusy === ice.position}
                        onClick={async () => {
                          if (translated) {
                            setIceTranslations((current) => {
                              const next = { ...current }
                              delete next[ice.position]
                              return next
                            })
                            return
                          }
                          setIceBusy(ice.position)
                          try {
                            const result = await api.translateText(
                              ice.question_fr,
                              'fr',
                              detail.other?.native_language ?? 'en',
                            )
                            setIceTranslations((current) => ({
                              ...current,
                              [ice.position]: result.translated,
                            }))
                          } catch {
                            setError('Traduction indisponible pour cette question.')
                          } finally {
                            setIceBusy(null)
                          }
                        }}
                      >
                        {translated ? 'voir en français' : 'voir en langue du correspondant'}
                      </button>
                    )}
                  </span>
                </li>
              )
            })}
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
              {wordTokens[message.id] ? (
                wordTokens[message.id]?.map((token, position) =>
                  /\p{L}/u.test(token) ? (
                    <button
                      key={position}
                      className="rounded px-0.5 hover:bg-white/10 hover:underline"
                      onClick={() => void lookUp(token)}
                    >
                      {token}
                    </button>
                  ) : (
                    <span key={position}>{token}</span>
                  ),
                )
              ) : reading[message.id]
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
              <button className="hover:underline" onClick={() => void toggleWordMode(message)}>
                {wordTokens[message.id] ? 'Quitter mot à mot' : 'Mot à mot'}
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

      {lexPanel && (
        <aside className="rise mt-3 rounded-2xl border border-white/10 bg-[color:var(--ink-850)] p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="display text-lg">{lexPanel.word}</p>
              {lexPanel.reading && (
                <p className="text-xs text-white/45">
                  {lexPanel.reading.kana} · {lexPanel.reading.romaji}
                </p>
              )}
            </div>
            <button
              className="text-xs text-white/40 hover:text-white/70"
              onClick={() => setLexPanel(null)}
            >
              Fermer
            </button>
          </div>
          {lexPanel.senses.length === 0 ? (
            <p className="mt-2 text-sm text-white/50">Aucun sens trouvé pour ce mot.</p>
          ) : (
            <ol className="mt-3 flex list-decimal flex-col gap-1.5 pl-5 text-sm text-white/75">
              {lexPanel.senses.map((sense, index) => (
                <li key={index}>
                  {sense.part_of_speech !== '—' && (
                    <span className="text-white/40">[{sense.part_of_speech}] </span>
                  )}
                  {sense.definition}
                </li>
              ))}
            </ol>
          )}
          <p className="mt-3 text-[11px] text-white/30">
            {lexPanel.source === 'wiktionnaire'
              ? 'Source : Wiktionnaire francophone'
              : 'Source indisponible — aucune définition affichée'}
            {lexBusy && ' · recherche…'}
          </p>
        </aside>
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
