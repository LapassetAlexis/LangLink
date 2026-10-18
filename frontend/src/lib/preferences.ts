import type { Preferences } from './api'

/** Applique les préférences sur `<html>` : densité, taille, animations. */
export function applyPreferences(preferences: Preferences): void {
  const root = document.documentElement
  root.dataset.density = preferences.density
  root.dataset.textSize = preferences.text_size
  root.dataset.motion =
    preferences.motion === 'system'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
        ? 'reduce'
        : 'normal'
      : preferences.motion
}
