import type { ComponentType, SVGProps } from 'react'

import CN from 'country-flag-icons/react/3x2/CN'
import DE from 'country-flag-icons/react/3x2/DE'
import ES from 'country-flag-icons/react/3x2/ES'
import FR from 'country-flag-icons/react/3x2/FR'
import GB from 'country-flag-icons/react/3x2/GB'
import IT from 'country-flag-icons/react/3x2/IT'
import JP from 'country-flag-icons/react/3x2/JP'
import KR from 'country-flag-icons/react/3x2/KR'
import NL from 'country-flag-icons/react/3x2/NL'
import PT from 'country-flag-icons/react/3x2/PT'
import RU from 'country-flag-icons/react/3x2/RU'
import SA from 'country-flag-icons/react/3x2/SA'
import TR from 'country-flag-icons/react/3x2/TR'

type FlagComponent = ComponentType<SVGProps<SVGSVGElement>>

/** Drapeaux réellement utilisés : seuls ceux-ci entrent dans le bundle. */
// Le paquet déclare ses composants avec un type JSX propre, incompatible en surface avec
// `ComponentType<SVGProps<…>>` : on normalise à l'insertion plutôt que de caster à l'usage.
const asFlag = (component: unknown) => component as FlagComponent

const FLAGS: Record<string, FlagComponent> = {
  FR: asFlag(FR),
  GB: asFlag(GB),
  ES: asFlag(ES),
  DE: asFlag(DE),
  IT: asFlag(IT),
  PT: asFlag(PT),
  JP: asFlag(JP),
  KR: asFlag(KR),
  SA: asFlag(SA),
  RU: asFlag(RU),
  TR: asFlag(TR),
  NL: asFlag(NL),
  CN: asFlag(CN),
}

interface Props {
  /** Code pays ISO 3166-1 alpha-2 (FR, JP…). */
  country: string
  className?: string
}

/**
 * Drapeau vectoriel. Décoratif par défaut (`aria-hidden`) : le nom de la langue est
 * toujours affiché à côté, et c'est lui qui porte l'information.
 */
export function Flag({ country, className = '' }: Props) {
  const Component = FLAGS[country.toUpperCase()]
  if (!Component) {
    return (
      <span
        aria-hidden="true"
        className={`inline-block h-3.5 w-5 rounded-sm bg-white/10 ${className}`}
      />
    )
  }
  return (
    <Component
      aria-hidden="true"
      focusable="false"
      className={`inline-block h-3.5 w-5 rounded-[2px] align-[-2px] shadow-[0_0_0_1px_rgba(255,255,255,0.12)] ${className}`}
    />
  )
}
