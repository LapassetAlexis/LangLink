import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { LanguagePair } from '../components/LanguagePair'
import { LANGUAGES } from '../lib/languages'
import { levelOptions, levelTooltip } from '../lib/levels'
import { api, DEFAULT_PREFERENCES, setToken, type Preferences, type ProfileOut } from '../lib/api'
import { applyPreferences } from '../lib/preferences'

export function SettingsPage() {
  const navigate = useNavigate()
  const [profile, setProfile] = useState<ProfileOut | null>(null)
  const [blocks, setBlocks] = useState<Array<{ blocked_id: string; display_name: string }>>([])
  const [name, setName] = useState('')
  const [bio, setBio] = useState('')
  const [native, setNative] = useState('fr')
  const [target, setTarget] = useState('ja')
  const [level, setLevel] = useState('A2')
  const [password, setPassword] = useState('')
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [prefs, setPrefs] = useState<Preferences>(DEFAULT_PREFERENCES)

  useEffect(() => {
    void Promise.all([api.profile(), api.blocks(), api.preferences()])
      .then(([current, blocked, stored]) => {
        setPrefs({ ...DEFAULT_PREFERENCES, ...stored.preferences })
        setProfile(current)
        setName(current.display_name)
        setBio(current.bio ?? '')
        setNative(current.native_language ?? 'fr')
        setTarget(current.target_language ?? 'ja')
        setLevel(current.target_level ?? 'A2')
        setBlocks(blocked.items)
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Erreur'))
  }, [])

  async function saveProfile(event: React.FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      const updated = await api.setProfile(name, bio || null)
      setProfile(updated as unknown as ProfileOut)
      setNotice('Profil enregistré.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur')
    }
  }

  async function saveLanguages() {
    setError(null)
    try {
      await api.setLanguages(native, target, level)
      setNotice('Langues enregistrées.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur')
    }
  }

  async function logout() {
    await api.logout().catch(() => undefined)
    setToken(null)
    navigate('/')
  }

  async function removeAccount() {
    setError(null)
    try {
      await api.deleteAccount(password)
      setToken(null)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Suppression refusée')
    }
  }

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="display text-3xl">Réglages</h1>
        <Link className="btn-ghost" to="/discover">
          Retour
        </Link>
      </header>

      {notice && (
        <p role="status" className="rounded-2xl bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
          {notice}
        </p>
      )}
      {error && (
        <p role="alert" className="rounded-2xl bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      )}

      <section className="surface p-6">
        <h2 className="display text-xl">Affichage</h2>
        <p className="mt-1 text-sm text-white/45">
          Ces réglages s&apos;appliquent à toute l&apos;application.
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="flex flex-col gap-1.5 text-sm text-white/60">
            Densité
            <select
              className="field"
              value={prefs.density}
              onChange={(e) => setPrefs({ ...prefs, density: e.target.value as Preferences['density'] })}
            >
              <option value="confort">Confort</option>
              <option value="compact">Compact</option>
            </select>
          </label>
          <label className="flex flex-col gap-1.5 text-sm text-white/60">
            Taille du texte
            <select
              className="field"
              value={prefs.text_size}
              onChange={(e) => setPrefs({ ...prefs, text_size: e.target.value as Preferences['text_size'] })}
            >
              <option value="normal">Normale</option>
              <option value="large">Grande</option>
            </select>
          </label>
          <label className="flex flex-col gap-1.5 text-sm text-white/60">
            Animations
            <select
              className="field"
              value={prefs.motion}
              onChange={(e) => setPrefs({ ...prefs, motion: e.target.value as Preferences['motion'] })}
            >
              <option value="system">Suivre le système</option>
              <option value="normal">Normales</option>
              <option value="reduce">Réduites</option>
            </select>
          </label>
          <label className="flex items-center gap-3 text-sm text-white/60">
            <input
              type="checkbox"
              checked={prefs.furigana_auto}
              onChange={(e) => setPrefs({ ...prefs, furigana_auto: e.target.checked })}
            />
            Furigana automatique
          </label>
          <label className="flex items-center gap-3 text-sm text-white/60">
            <input
              type="checkbox"
              checked={prefs.word_mode_default}
              onChange={(e) => setPrefs({ ...prefs, word_mode_default: e.target.checked })}
            />
            Mode mot à mot par défaut
          </label>
        </div>
        <button
          className="btn-primary mt-4"
          onClick={async () => {
            try {
              const saved = await api.savePreferences(prefs)
              setPrefs({ ...DEFAULT_PREFERENCES, ...saved.preferences })
              applyPreferences(prefs)
              setNotice('Préférences enregistrées.')
            } catch (err) {
              setError(err instanceof Error ? err.message : 'Erreur')
            }
          }}
        >
          Enregistrer les préférences
        </button>
      </section>

      <section className="surface p-6">
        <h2 className="display text-xl">Profil</h2>
        <form className="mt-4 flex flex-col gap-4" onSubmit={saveProfile}>
          <label className="flex flex-col gap-1.5 text-sm text-white/60">
            Nom affiché
            <input className="field" value={name} maxLength={40} onChange={(e) => setName(e.target.value)} />
          </label>
          <label className="flex flex-col gap-1.5 text-sm text-white/60">
            Biographie
            <textarea
              className="field min-h-24"
              value={bio}
              maxLength={600}
              onChange={(e) => setBio(e.target.value)}
            />
            <span className="text-xs text-white/30">{bio.length}/600</span>
          </label>
          <button className="btn-primary self-start" type="submit">
            Enregistrer
          </button>
        </form>
      </section>

      <section className="surface p-6">
        <h2 className="display text-xl">Langues</h2>
        <p className="mt-1 text-sm text-white/45">
          {profile && (
            <LanguagePair native={profile.native_language} target={profile.target_language} />
          )}
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="flex flex-col gap-1.5 text-sm text-white/60">
            Ma langue maternelle
            <select className="field" value={native} onChange={(e) => setNative(e.target.value)}>
              {LANGUAGES.map((language) => (
                <option key={language.code} value={language.code}>
                  {language.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1.5 text-sm text-white/60">
            Langue apprise
            <select className="field" value={target} onChange={(e) => setTarget(e.target.value)}>
              {LANGUAGES.map((language) => (
                <option key={language.code} value={language.code}>
                  {language.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {levelOptions(target).map((option) => (
            <button
              key={option.code}
              type="button"
              title={levelTooltip(option.code, target)}
              onClick={() => setLevel(option.code)}
              className={option.code === level ? 'btn-primary px-4 py-2' : 'btn-ghost px-4 py-2'}
            >
              {option.label}
            </button>
          ))}
        </div>
        <button className="btn-primary mt-4" onClick={saveLanguages}>
          Enregistrer les langues
        </button>
      </section>

      <section className="surface p-6">
        <h2 className="display text-xl">Profils bloqués</h2>
        {blocks.length === 0 ? (
          <p className="mt-2 text-sm text-white/45">Aucun profil bloqué.</p>
        ) : (
          <ul className="mt-3 flex flex-col gap-2">
            {blocks.map((blocked) => (
              <li key={blocked.blocked_id} className="flex items-center justify-between text-sm">
                <span>{blocked.display_name}</span>
                <button
                  className="text-white/40 underline underline-offset-4 hover:text-white/70"
                  onClick={() =>
                    void api.block(blocked.blocked_id).then(() => undefined)
                  }
                >
                  Débloquer
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="surface border-red-500/20 p-6">
        <h2 className="display text-xl text-red-200">Zone sensible</h2>
        <p className="mt-2 text-sm text-white/45">
          La suppression anonymise votre compte sous 30 jours. Vos messages restent lisibles
          sous « Compte supprimé ».
        </p>
        <label className="mt-4 flex flex-col gap-1.5 text-sm text-white/60">
          Confirmez avec votre mot de passe
          <input
            className="field"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <div className="mt-4 flex gap-3">
          <button className="btn-ghost" onClick={() => void logout()}>
            Se déconnecter
          </button>
          <button
            className="btn border border-red-500/40 px-5 text-red-200 hover:border-red-400"
            onClick={() => void removeAccount()}
            disabled={password.length < 10}
          >
            Supprimer mon compte
          </button>
        </div>
      </section>
    </main>
  )
}
