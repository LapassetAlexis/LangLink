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
  /** Fuseau de secours quand le profil n'en fournit aucun. */
  defaultTimezone: string
}

export const LANGUAGES: LanguageInfo[] = [
  { code: 'fr', label: 'Français', country: 'FR', defaultTimezone: 'Europe/Paris' },
  { code: 'en', label: 'Anglais', country: 'GB', defaultTimezone: 'Europe/London' },
  { code: 'es', label: 'Espagnol', country: 'ES', defaultTimezone: 'Europe/Madrid' },
  { code: 'de', label: 'Allemand', country: 'DE', defaultTimezone: 'Europe/Berlin' },
  { code: 'it', label: 'Italien', country: 'IT', defaultTimezone: 'Europe/Rome' },
  { code: 'pt', label: 'Portugais', country: 'PT', defaultTimezone: 'Europe/Lisbon' },
  { code: 'ja', label: 'Japonais', country: 'JP', defaultTimezone: 'Asia/Tokyo' },
  { code: 'ko', label: 'Coréen', country: 'KR', defaultTimezone: 'Asia/Seoul' },
  { code: 'ar', label: 'Arabe', country: 'SA', defaultTimezone: 'Asia/Riyadh' },
  { code: 'ru', label: 'Russe', country: 'RU', defaultTimezone: 'Europe/Moscow' },
  { code: 'tr', label: 'Turc', country: 'TR', defaultTimezone: 'Europe/Istanbul' },
  { code: 'nl', label: 'Néerlandais', country: 'NL', defaultTimezone: 'Europe/Amsterdam' },
  { code: 'zh-Hans', label: 'Chinois', country: 'CN', defaultTimezone: 'Asia/Shanghai' },
]

const BY_CODE = new Map(LANGUAGES.map((language) => [language.code.toLowerCase(), language]))

export function languageInfo(code: string | null | undefined): LanguageInfo {
  if (!code) return { code: '', label: 'Langue inconnue', country: '', defaultTimezone: '' }
  return (
    BY_CODE.get(code.toLowerCase()) ?? {
      code,
      label: code.toUpperCase(),
      country: '',
      defaultTimezone: '',
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

/** Fuseau de secours déduit de la langue, quand le profil n'en fournit aucun. */
export function defaultTimezoneOf(code: string | null | undefined): string | null {
  const timezone = languageInfo(code).defaultTimezone
  return timezone || null
}
