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
  /** Code pays ISO 3166-1 alpha-2, utilisé pour le drapeau SVG. */
  country: string
}

export const LANGUAGES: LanguageInfo[] = [
  { code: 'fr', label: 'Français', country: 'FR' },
  { code: 'en', label: 'Anglais', country: 'GB' },
  { code: 'es', label: 'Espagnol', country: 'ES' },
  { code: 'de', label: 'Allemand', country: 'DE' },
  { code: 'it', label: 'Italien', country: 'IT' },
  { code: 'pt', label: 'Portugais', country: 'PT' },
  { code: 'ja', label: 'Japonais', country: 'JP' },
  { code: 'ko', label: 'Coréen', country: 'KR' },
  { code: 'ar', label: 'Arabe', country: 'SA' },
  { code: 'ru', label: 'Russe', country: 'RU' },
  { code: 'tr', label: 'Turc', country: 'TR' },
  { code: 'nl', label: 'Néerlandais', country: 'NL' },
  { code: 'zh-Hans', label: 'Chinois', country: 'CN' },
]

const BY_CODE = new Map(LANGUAGES.map((language) => [language.code.toLowerCase(), language]))

export function languageInfo(code: string | null | undefined): LanguageInfo {
  if (!code) return { code: '', label: 'Langue inconnue', country: '' }
  return (
    BY_CODE.get(code.toLowerCase()) ?? {
      code,
      label: code.toUpperCase(),
      country: '',
    }
  )
}

export function countryOf(code: string | null | undefined): string {
  return languageInfo(code).country
}

export function labelOf(code: string | null | undefined): string {
  return languageInfo(code).label
}

/** Analyse une paire déjà formatée par l'API, du type « ja → fr ». */
export function parsePair(value: string): [string, string] {
  const [left, right] = value.split('→').map((part) => part.trim())
  return [left ?? '', right ?? '']
}
