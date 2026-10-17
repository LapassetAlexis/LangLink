/**
 * Référentiel d'affichage des langues : code BCP-47 → libellé + drapeau.
 *
 * Le drapeau est un *repère visuel*, jamais la seule information : le libellé reste
 * présent pour les lecteurs d'écran et pour les systèmes qui ne rendent pas les emoji
 * (Windows notamment affiche les indicatifs régionaux en lettres).
 */

export interface LanguageInfo {
  code: string
  label: string
  flag: string
}

export const LANGUAGES: LanguageInfo[] = [
  { code: 'fr', label: 'Français', flag: '🇫🇷' },
  { code: 'en', label: 'Anglais', flag: '🇬🇧' },
  { code: 'es', label: 'Espagnol', flag: '🇪🇸' },
  { code: 'de', label: 'Allemand', flag: '🇩🇪' },
  { code: 'it', label: 'Italien', flag: '🇮🇹' },
  { code: 'pt', label: 'Portugais', flag: '🇵🇹' },
  { code: 'ja', label: 'Japonais', flag: '🇯🇵' },
  { code: 'ko', label: 'Coréen', flag: '🇰🇷' },
  { code: 'ar', label: 'Arabe', flag: '🇸🇦' },
  { code: 'ru', label: 'Russe', flag: '🇷🇺' },
  { code: 'tr', label: 'Turc', flag: '🇹🇷' },
  { code: 'nl', label: 'Néerlandais', flag: '🇳🇱' },
  { code: 'zh-Hans', label: 'Chinois', flag: '🇨🇳' },
]

const BY_CODE = new Map(LANGUAGES.map((language) => [language.code.toLowerCase(), language]))

export function languageInfo(code: string | null | undefined): LanguageInfo {
  if (!code) return { code: '', label: 'Langue inconnue', flag: '🏳️' }
  return (
    BY_CODE.get(code.toLowerCase()) ?? {
      code,
      label: code.toUpperCase(),
      flag: '🏳️',
    }
  )
}

export function flagOf(code: string | null | undefined): string {
  return languageInfo(code).flag
}

export function labelOf(code: string | null | undefined): string {
  return languageInfo(code).label
}

/** « 🇫🇷 → 🇯🇵 » à partir de deux codes. */
export function pairFlags(native: string | null | undefined, target: string | null | undefined): string {
  return `${flagOf(native)} → ${flagOf(target)}`
}

/** Analyse une paire déjà formatée par l'API, du type « ja → fr ». */
export function parsePair(value: string): [string, string] {
  const [left, right] = value.split('→').map((part) => part.trim())
  return [left ?? '', right ?? '']
}
