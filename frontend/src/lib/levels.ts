/**
 * Niveaux d'apprentissage : libellés lisibles, échelles par langue cible.
 *
 * Le stockage reste un code CEFR (`A1`…`C2`) : c'est l'échelle sur laquelle le score
 * d'affinité est calculé côté SQL. Ce module ne fait que l'habiller.
 */

export interface LevelOption {
  /** Code stocké en base. */
  code: string
  /** Libellé affiché à l'utilisateur. */
  label: string
  /** Référentiel d'origine, pour l'infobulle. */
  scale: 'cefr' | 'jlpt'
}

const GENERIC: LevelOption[] = [
  { code: 'A1', label: 'Débutant', scale: 'cefr' },
  { code: 'A2', label: 'Débutant avancé', scale: 'cefr' },
  { code: 'B1', label: 'Intermédiaire', scale: 'cefr' },
  { code: 'B2', label: 'Confirmé', scale: 'cefr' },
  { code: 'C1', label: 'Avancé', scale: 'cefr' },
  { code: 'C2', label: 'Maîtrise', scale: 'cefr' },
]

/**
 * Surcharges par langue cible. La correspondance JLPT ↔ CECR est **indicative** : le JLPT
 * mesure la compréhension, le CECR évalue aussi la production.
 */
const OVERRIDES: Record<string, LevelOption[]> = {
  ja: [
    { code: 'A1', label: 'N5 · Débutant', scale: 'jlpt' },
    { code: 'A2', label: 'N4 · Élémentaire', scale: 'jlpt' },
    { code: 'B1', label: 'N3 · Intermédiaire', scale: 'jlpt' },
    { code: 'B2', label: 'N2 · Confirmé', scale: 'jlpt' },
    { code: 'C1', label: 'N1 · Avancé', scale: 'jlpt' },
    { code: 'C2', label: 'N1+ · Maîtrise', scale: 'jlpt' },
  ],
  ko: [
    { code: 'A1', label: 'TOPIK 1 · Débutant', scale: 'cefr' },
    { code: 'A2', label: 'TOPIK 2 · Élémentaire', scale: 'cefr' },
    { code: 'B1', label: 'TOPIK 3 · Intermédiaire', scale: 'cefr' },
    { code: 'B2', label: 'TOPIK 4 · Confirmé', scale: 'cefr' },
    { code: 'C1', label: 'TOPIK 5 · Avancé', scale: 'cefr' },
    { code: 'C2', label: 'TOPIK 6 · Maîtrise', scale: 'cefr' },
  ],
}

/** Options de niveau pour une langue cible donnée. */
export function levelOptions(targetLanguage: string | null | undefined): LevelOption[] {
  const code = (targetLanguage ?? '').toLowerCase()
  return OVERRIDES[code] ?? GENERIC
}

/** Libellé d'un code stocké, dans l'échelle de la langue cible. */
export function levelLabel(code: string | null | undefined, targetLanguage?: string | null): string {
  if (!code) return 'niveau non défini'
  const option = levelOptions(targetLanguage).find((entry) => entry.code === code)
  return option ? option.label : code
}

/** Infobulle : toujours le code CEFR, jamais l'inverse. */
export function levelTooltip(
  code: string | null | undefined,
  targetLanguage?: string | null,
): string {
  if (!code) return ''
  const option = levelOptions(targetLanguage).find((entry) => entry.code === code)
  if (!option) return code
  return option.scale === 'jlpt'
    ? `${code} (équivalence indicative JLPT → CECR)`
    : `CECR ${code}`
}
