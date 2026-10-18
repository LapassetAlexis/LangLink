import { useState } from 'react'

import { api } from '../lib/api'
import { labelOf } from '../lib/languages'

interface Props {
  /** Ma langue maternelle (= ce que le correspondant apprend). */
  mine: string | null | undefined
  /** Langue maternelle du correspondant (= ce que j'apprends). */
  theirs: string | null | undefined
  onInsert: (text: string) => void
}

/**
 * Tiroir d'assistance à la traduction, dans les deux sens de la conversation.
 *
 * Aucun modèle de langage : moteur déterministe auto-hébergé, provenance affichée
 * (REQ-PLT-08). Ce n'est pas un interlocuteur, seulement un outil.
 */
export function AssistDock({ mine, theirs, onInsert }: Props) {
  const [open, setOpen] = useState(false)
  const [towardsThem, setTowardsThem] = useState(true)
  const [text, setText] = useState('')
  const [result, setResult] = useState<{ translated: string; provider: string } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const source = towardsThem ? (mine ?? 'fr') : (theirs ?? 'ja')
  const target = towardsThem ? (theirs ?? 'ja') : (mine ?? 'fr')

  function reset(): void {
    setOpen(false)
    setResult(null)
    setError(null)
  }

  async function translate() {
    const value = text.trim()
    if (!value || !source || !target) return
    setBusy(true)
    setError(null)
    try {
      const response = await api.translateText(value, source, target)
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
            Moteur déterministe, aucun modèle de langage
          </p>
        </div>
        <button className="text-xs text-white/40 hover:text-white/70" onClick={reset}>
          Fermer
        </button>
      </header>

      <div className="mt-3 flex items-center gap-2">
        <div
          role="group"
          aria-label="Sens de la traduction"
          className="flex rounded-full border border-white/10 p-0.5 text-xs"
        >
          <button
            type="button"
            aria-pressed={towardsThem}
            className={`rounded-full px-3 py-1.5 transition ${
              towardsThem ? 'bg-brand-500 font-medium text-[color:var(--ink-950)]' : 'text-white/55'
            }`}
            onClick={() => {
              setTowardsThem(true)
              setResult(null)
            }}
          >
            {labelOf(source)} → {labelOf(theirs)}
          </button>
          <button
            type="button"
            aria-pressed={!towardsThem}
            className={`rounded-full px-3 py-1.5 transition ${
              !towardsThem ? 'bg-brand-500 font-medium text-[color:var(--ink-950)]' : 'text-white/55'
            }`}
            onClick={() => {
              setTowardsThem(false)
              setResult(null)
            }}
          >
            {labelOf(theirs)} → {labelOf(mine)}
          </button>
        </div>
      </div>

      <p className="mt-2 text-[11px] text-white/30">
        Traduction vers le {labelOf(target).toLowerCase()} · {labelOf(source)} en entrée
      </p>

      <textarea
        className="field mt-2 min-h-16 resize-y text-sm"
        placeholder={
          towardsThem
            ? 'Ce que tu veux dire, en français…'
            : 'Ce que tu veux comprendre, en japonais…'
        }
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
