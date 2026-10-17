import { Flag } from './Flag'
import { countryOf, languageInfo, parsePair } from '../lib/languages'

interface Props {
  native?: string | null
  target?: string | null
  /** Paire déjà formatée par l'API (« ja → fr »), utilisée si native/target sont absents. */
  pair?: string
  className?: string
}

/**
 * Affiche une paire de langues : drapeau SVG + libellé en toutes lettres.
 * Le texte accessible reste explicite (« Japonais vers Français ») ; les drapeaux sont
 * décoratifs, jamais porteurs d'information seuls.
 */
export function LanguagePair({ native, target, pair, className = '' }: Props) {
  const [left, right] = pair ? parsePair(pair) : [native, target]
  const source = languageInfo(left)
  const destination = languageInfo(right)

  return (
    <span
      className={`inline-flex items-center gap-1.5 ${className}`}
      aria-label={`${source.label} vers ${destination.label}`}
      title={`${source.label} → ${destination.label}`}
    >
      <Flag country={countryOf(left)} />
      <span className="lowercase">{source.label}</span>
      <span aria-hidden="true" className="opacity-40">
        →
      </span>
      <Flag country={countryOf(right)} />
      <span className="lowercase">{destination.label}</span>
    </span>
  )
}
