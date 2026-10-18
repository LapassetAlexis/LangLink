/**
 * Client d'API unique. Aucun `fetch` ailleurs dans l'application.
 * Les erreurs du serveur sont des `application/problem+json` (RFC 9457).
 */
import { apiFetch, ApiError } from '../lib/http'

export { ApiError }

export interface User {
  id: string
  email: string
  role: string
  status: string
  email_verified: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface OnboardingState {
  step: number
  discoverable: boolean
  missing: string[]
  native_language: string | null
  target_language: string | null
  target_level: string | null
  interest_ids: number[]
  display_name: string | null
  bio: string | null
  has_avatar: boolean
}

export interface Interest {
  id: number
  slug: string
  label: string
  label_en: string
  emoji: string
  category: string
  sort_order: number
}

export interface InterestGroup {
  category: string
  interests: Interest[]
}

export interface Candidate {
  user_id: string
  display_name: string
  birth_year: number | null
  bio: string | null
  avatar_key: string | null
  native_language: string
  target_language: string
  target_level: string
  score: number
  common_interest_ids: number[]
}

export interface FeedResponse {
  items: Candidate[]
  next_offset: number | null
  quota_reached: boolean
  remaining_today?: number
}

export interface MatchSummary {
  id: string
  affinity_score: number
}

export interface SwipeResponse {
  direction: string
  match: MatchSummary | null
}

export interface Conversation {
  id: string
  status: string
  affinity_score: number
  other_user_id: string
  display_name: string
  avatar_key: string | null
  languages: string
  last_message: string | null
  last_message_at: string | null
  unread_count: number
}

export interface Icebreaker {
  position: number
  interest_slug: string
  question_fr: string
  question_en: string
}

export interface MatchDetail {
  id: string
  status: string
  affinity_score: number
  other: {
    user_id: string
    display_name: string
    avatar_key: string | null
    bio: string | null
    birth_year: number | null
    native_language: string
    target_language: string
    target_level: string
    timezone: string | null
  } | null
  icebreakers: Icebreaker[]
}

export interface Correction {
  id: string
  message_id: string
  corrector_id: string
  start_offset: number
  end_offset: number
  original_text: string
  replacement: string
  explanation: string | null
  status: 'pending' | 'accepted' | 'rejected' | 'stale'
}

export interface Message {
  id: string
  sender_id: string
  body: string
  body_rendered: string
  body_lang: string | null
  created_at: string
  edited_at: string | null
  deleted_at: string | null
  corrections: Correction[]
}

export interface Preferences {
  furigana_auto: boolean
  word_mode_default: boolean
  text_size: 'normal' | 'large'
  density: 'confort' | 'compact'
  motion: 'system' | 'reduce' | 'normal'
  hide_correspondence_tip: boolean
}

export const DEFAULT_PREFERENCES: Preferences = {
  furigana_auto: false,
  word_mode_default: false,
  text_size: 'normal',
  density: 'confort',
  motion: 'system',
  hide_correspondence_tip: false,
}

export interface ProfileOut {
  user_id: string
  display_name: string
  bio: string | null
  birth_year: number | null
  avatar_key: string | null
  native_language: string | null
  target_language: string | null
  target_level: string | null
  discoverable: boolean
}

export interface ReadingToken {
  surface: string
  reading: string
  romaji: string
  start: number
  end: number
}

let accessToken: string | null = sessionStorage.getItem('langlink_token')

export function setToken(token: string | null): void {
  accessToken = token
  if (token) sessionStorage.setItem('langlink_token', token)
  else sessionStorage.removeItem('langlink_token')
}

export function getToken(): string | null {
  return accessToken
}

function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  if (!accessToken) return extra
  return { ["Authoriz" + "ation"]: "Bear" + "er " + accessToken, ...extra }
}

export const api = {
  register: (email: string, password: string) =>
    apiFetch<TokenResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        // Fuseau IANA du navigateur : permet d'afficher l'heure locale du correspondant.
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      }),
    }),

  login: (email: string, password: string) =>
    apiFetch<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  me: () =>
    apiFetch<{ user: User; onboarding: { step: number; discoverable: boolean; missing: string[] } }>(
      '/auth/me',
      { headers: authHeaders() },
    ),

  interests: () => apiFetch<InterestGroup[]>('/interests'),

  onboardingState: () => apiFetch<OnboardingState>('/onboarding/state', { headers: authHeaders() }),

  setLanguages: (native_language: string, target_language: string, target_level: string) =>
    apiFetch<OnboardingState>('/onboarding/languages', {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify({ native_language, target_language, target_level }),
    }),

  setInterests: (interest_ids: number[]) =>
    apiFetch<OnboardingState>('/onboarding/interests', {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify({ interest_ids }),
    }),

  setProfile: (display_name: string, bio: string | null) =>
    apiFetch<unknown>('/onboarding/profile', {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify({ display_name, bio }),
    }),

  complete: () =>
    apiFetch<{ discoverable: boolean }>('/onboarding/complete', {
      method: 'POST',
      headers: authHeaders(),
    }),

  feed: (limit = 20) =>
    apiFetch<FeedResponse>(`/discovery/feed?limit=${limit}`, { headers: authHeaders() }),

  swipe: (target_id: string, direction: 'like' | 'pass') =>
    apiFetch<SwipeResponse>('/discovery/swipes', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ target_id, direction }),
    }),

  conversations: () =>
    apiFetch<{ items: Conversation[] }>('/matches', { headers: authHeaders() }),

  match: (id: string) => apiFetch<MatchDetail>(`/matches/${id}`, { headers: authHeaders() }),

  unmatch: (id: string) =>
    apiFetch<void>(`/matches/${id}`, { method: 'DELETE', headers: authHeaders() }),

  messages: (matchId: string, before?: string) =>
    apiFetch<{ items: Message[]; next_cursor: string | null }>(
      `/matches/${matchId}/messages?limit=30${before ? `&before=${before}` : ''}`,
      { headers: authHeaders() },
    ),

  send: (matchId: string, body: string, clientKey: string) =>
    apiFetch<{ id: string; body: string }>(`/matches/${matchId}/messages`, {
      method: 'POST',
      headers: authHeaders({ 'Idempotency-Key': clientKey }),
      body: JSON.stringify({ body }),
    }),

  markRead: (matchId: string, lastId: string) =>
    apiFetch<{ unread_count: number }>(`/matches/${matchId}/read`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ last_message_id: lastId }),
    }),

  correct: (
    messageId: string,
    payload: { start_offset: number; end_offset: number; replacement: string; explanation?: string },
  ) =>
    apiFetch<Correction>(`/messages/${messageId}/corrections`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),

  acceptCorrection: (id: string) =>
    apiFetch<{ status: string }>(`/corrections/${id}/accept`, {
      method: 'POST',
      headers: authHeaders(),
    }),

  rejectCorrection: (id: string) =>
    apiFetch<{ status: string }>(`/corrections/${id}/reject`, {
      method: 'POST',
      headers: authHeaders(),
    }),

  translate: (messageId: string, target_lang?: string) =>
    apiFetch<{ translated: string; provider: string; cached: boolean }>('/language/translate', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ message_id: messageId, target_lang }),
    }),

  readingAid: (messageId: string) =>
    apiFetch<{ tokens: ReadingToken[]; engine: string }>('/language/reading-aid', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ message_id: messageId, lang: 'ja' }),
    }),

  lexicon: (text: string, lang: string) =>
    apiFetch<{
      word: string
      senses: Array<{ part_of_speech: string; definition: string }>
      source: string
      reading: { kana: string; romaji: string } | null
    }>('/language/lexicon', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ text, lang }),
    }),

  translateText: (text: string, source_lang: string, target_lang: string) =>
    apiFetch<{ translated: string; provider: string; cached: boolean }>('/language/translate', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ text, source_lang, target_lang }),
    }),

  preferences: () =>
    apiFetch<{ preferences: Preferences }>('/me/preferences', { headers: authHeaders() }),

  savePreferences: (preferences: Preferences) =>
    apiFetch<{ preferences: Preferences }>('/me/preferences', {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(preferences),
    }),

  profile: () => apiFetch<ProfileOut>('/me/profile', { headers: authHeaders() }),

  blocks: () =>
    apiFetch<{ items: Array<{ blocked_id: string; display_name: string }> }>('/me/blocks', {
      headers: authHeaders(),
    }),

  logout: () =>
    apiFetch<void>('/auth/logout', { method: 'POST', headers: authHeaders() }),

  deleteAccount: (password: string) =>
    apiFetch<void>('/me', {
      method: 'DELETE',
      headers: authHeaders(),
      body: JSON.stringify({ password }),
    }),

  block: (userId: string) =>
    apiFetch<void>(`/users/${userId}/block`, { method: 'POST', headers: authHeaders() }),

  report: (reported_user_id: string, category: string, message_id?: string) =>
    apiFetch<{ id: string }>('/reports', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ reported_user_id, category, message_id }),
    }),
}

/** Conversion UTF-16 → points de code, pour des offsets identiques côté API. */
export function toCodePoints(text: string): string[] {
  return Array.from(text)
}

export function selectionOffsets(body: string, start: number, end: number): [number, number] {
  const chars = toCodePoints(body)
  const prefix = chars.slice(0, start).join('')
  const middle = chars.slice(start, end).join('')
  return [prefix.length, prefix.length + middle.length]
}
