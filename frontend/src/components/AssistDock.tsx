import { useState } from 'react'

import { api } from '../lib/api'

interface Props {
  /** Langue du correspondant : cible de la traduction. */
  targetLang: string | null | undefined
  /** Langue du lecteur : langue source. */
  sourceLang?: string | null
  onInsert: (text: string) => void
}

/**
 * Tiroir d'assistance à la traduction (aucun modèle de langage).
 *
 * Ce n'est pas un agent : il ne comprend rien, il ne répond pas, il ne rédige pas. Il envoie
 * le texte à un moteur déterministe (LibreTranslate auto-hébergé) et affiche le résultat avec
 * sa provenance — exigence REQ-PLT-08.
 */
export function AssistDock({ targetLang, sourceLang = 'fr', onInsert }: Props) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const [result, setResult] = useState<{ translated: string; provider: string } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function translate() {
    const value = text.trim()
    if (!value || !targetLang) return
    setBusy(true)
    setError(null)
    try {
      const response = await api.translateText(value, sourceLang ?? 'fr', targetLang)
      setResult({ translated: response.translated, provider: response.provider })
    } catch {
      setError('Moteur de traduction indisponible.')
      setResult(null)
    } finally {
      setBusy(false)
    }
  }

  if (!open) {
    return (
      <div className="mt-3 flex justify-end">
        <button className="btn-ghost px-4 py-2 text-xs" onClick={() => setOpen(true)}>
          <span aria-hidden="true">⌗</span> Aide · traduire
        </button>
      </div>
    )
  }

  return (
    <aside className="rise mt-3 rounded-2xl border border-white/10 bg-[color:var(--ink-850)] p-4">
      <header className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-widest text-white/35">Aide à la traduction</p>
          <p className="mt-0.5 text-xs text-white/45">
            Vers {targetLang ?? '—'} · moteur déterministe, aucun modèle de langage
          </p>
        </div>
        <button
          className="text-xs text-white/40 hover:text-white/70"
          onClick={() => {
            setOpen(false)
            setResult(null)
            setError(null)
          }}
        >
          Fermer
        </button>
      </header>

      <textarea
        className="field mt-3 min-h-16 resize-y text-sm"
        placeholder="Colle une phrase, ou sélectionne-la dans un message…"
        maxLength={1200}
        value={text}
        onChange={(event) => setText(event.target.value)}
      />

      <div className="mt-2 flex flex-wrap items-center gap-2">
        <button
          className="btn-primary px-4 py-2 text-xs"
          disabled={busy || text.trim().length === 0}
          onClick={() => void translate()}
        >
          {busy ? 'Traduction…' : 'Traduire'}
        </button>
        {result && (
          <button
            className="btn-ghost px-4 py-2 text-xs"
            onClick={() => {
              onInsert(result.translated)
              setOpen(false)
            }}
          >
            Insérer dans mon message
          </button>
        )}
      </div>

      {error && (
        <p role="alert" className="mt-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {result && (
        <div className="mt-3 rounded-xl bg-white/[0.04] p-3">
          <p className="text-sm text-white/85">{result.translated}</p>
          <p className="mt-2 text-[11px] text-white/30">Moteur : {result.provider}</p>
        </div>
      )}
    </aside>
  )
}
