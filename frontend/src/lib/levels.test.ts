import { describe, expect, it } from 'vitest'

import { levelLabel, levelOptions, levelTooltip } from './levels'

describe('niveaux', () => {
  it('utilise les libellés génériques quand aucune échelle locale n’existe', () => {
    expect(levelLabel('B1', 'fr')).toBe('Intermédiaire')
    expect(levelLabel('C2', 'en')).toBe('Maîtrise')
    expect(levelOptions('fr').map((option) => option.code)).toEqual([
      'A1',
      'A2',
      'B1',
      'B2',
      'C1',
      'C2',
    ])
  })

  it('bascule sur le JLPT pour le japonais, sans perdre les codes stockés', () => {
    expect(levelLabel('B1', 'ja')).toBe('N3 · Intermédiaire')
    expect(levelOptions('ja').map((option) => option.code)).toEqual([
      'A1',
      'A2',
      'B1',
      'B2',
      'C1',
      'C2',
    ])
    expect(levelOptions('ja')[0]?.label).toContain('N5')
  })

  it('annonce l’équivalence JLPT comme indicative', () => {
    expect(levelTooltip('B1', 'ja')).toContain('indicative')
    expect(levelTooltip('B1', 'fr')).toBe('CECR B1')
  })

  it('retombe sur le code brut si la valeur est inconnue', () => {
    expect(levelLabel('Z9', 'fr')).toBe('Z9')
    expect(levelLabel(null)).toBe('niveau non défini')
  })
})
