/**
 * Coquille applicative du lot 1.
 *
 * Les écrans réels arrivent avec leurs capacités (onboarding, discovery, messages…).
 * Ce composant sert de preuve de vie : il doit se builder et se tester sans backend.
 */
export function App() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-6 px-6 py-16">
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-brand-400">LangLink</p>
      <h1 className="text-4xl font-semibold leading-tight sm:text-5xl">
        Échangez avec des personnes qui apprennent votre langue.
      </h1>
      <p className="max-w-xl text-lg text-slate-400">
        Correspondance asynchrone autour d&apos;intérêts communs. Pas de chatbot, pas de
        pression : des humains, des corrections bienveillantes, des outils pour comprendre.
      </p>
      <p className="text-sm text-slate-500">
        Squelette v0.1.0 — écrans à venir avec les capacités du change <code>mvp-v1</code>.
      </p>
    </main>
  )
}
