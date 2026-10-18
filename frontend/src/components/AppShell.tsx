import { Link, NavLink } from 'react-router-dom'

interface Props {
  children: React.ReactNode
  /** Largeur de contenu : la messagerie occupe toute la page, les formulaires sont bornés. */
  wide?: boolean
}

const TABS = [
  { to: '/discover', label: 'Découvrir' },
  { to: '/messages', label: 'Messages' },
  { to: '/settings', label: 'Mon compte' },
]

/** Coquille commune à toutes les vues authentifiées : en-tête, navigation, contenu. */
export function AppShell({ children, wide = false }: Props) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-20 border-b border-white/5 bg-[color:var(--ink-900)]/85 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between gap-6 px-5">
          <Link to="/discover" className="flex items-center gap-2.5 text-sm font-medium">
            <span
              aria-hidden="true"
              className="grid h-7 w-7 place-items-center rounded-full text-[12px] font-semibold text-[color:var(--ink-950)]"
              style={{ background: 'linear-gradient(160deg, var(--amber-400), var(--rose-400))' }}
            >
              L
            </span>
            <span className="hidden text-[color:var(--sand-100)] sm:block">LangLink</span>
          </Link>

          <nav aria-label="Navigation principale" className="flex items-center gap-1">
            {TABS.map((tab) => (
              <NavLink
                key={tab.to}
                to={tab.to}
                className={({ isActive }) =>
                  [
                    'rounded-full px-3.5 py-1.5 text-sm transition',
                    isActive
                      ? 'bg-white/[0.08] text-[color:var(--sand-100)]'
                      : 'text-white/50 hover:bg-white/[0.04] hover:text-white/80',
                  ].join(' ')
                }
              >
                {tab.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className={wide ? 'flex-1' : 'mx-auto w-full max-w-3xl flex-1 px-5 py-8'}>
        {children}
      </main>
    </div>
  )
}
