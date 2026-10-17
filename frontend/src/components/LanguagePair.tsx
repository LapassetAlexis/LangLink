import { languageInfo, parsePair } from '../lib/languages'

interface Props {
  native?: string | null
  target?: string | null
  /** Paire déjà formatée par l'API (« ja → fr »), utilisée si native/target sont absents. */
  pair?: string
  className?: string
}

/**
 * Affiche une paire de langues avec drapeaux.
 *
 * Le texte accessible reste explicite (« Japonais vers Français ») : les emoji ne sont
 * jamais la seule information.
 */
export function LanguagePair({ native, target, pair, className = '' }: Props) {
  const [left, right] = pair ? parsePair(pair) : [native, target]
  const source = languageInfo(left)
  const destination = languageInfo(right)

  return (
    <span
      className={className}
      aria-label={`${source.label} vers ${destination.label}`}
      title={`${source.label} → ${destination.label}`}
    >
      <span aria-hidden="true">
        {source.flag} {source.label.toLowerCase()}
      </span>
      <span aria-hidden="true" className="mx-1.5 opacity-40">
        →
      </span>
      <span aria-hidden="true">
        {destination.flag} {destination.label.toLowerCase()}
      </span>
    </span>
  )
}
