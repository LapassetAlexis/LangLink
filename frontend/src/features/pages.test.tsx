import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ChatPage, DiscoverPage, InboxPage, WizardPage } from './pages'

const apiMock = vi.hoisted(() => ({
  onboardingState: vi.fn(),
  interests: vi.fn(),
  setLanguages: vi.fn(),
  setInterests: vi.fn(),
  complete: vi.fn(),
  feed: vi.fn(),
  swipe: vi.fn(),
  conversations: vi.fn(),
  match: vi.fn(),
  messages: vi.fn(),
  send: vi.fn(),
  markRead: vi.fn(),
  translate: vi.fn(),
  lexicon: vi.fn(),
  readingAid: vi.fn(),
  correct: vi.fn(),
  acceptCorrection: vi.fn(),
  rejectCorrection: vi.fn(),
}))

vi.mock('../lib/api', () => ({
  api: apiMock,
  ApiError: class ApiError extends Error {
    problem = { type: 'x', title: 'Erreur', status: 400 }
  },
  getToken: () => 'jeton',
  setToken: vi.fn(),
  toCodePoints: (text: string) => Array.from(text),
  selectionOffsets: (text: string, start: number, end: number) => [
    Array.from(text).slice(0, start).join('').length,
    Array.from(text).slice(0, end).join('').length,
  ],
}))

const STATE = {
  step: 1,
  discoverable: false,
  missing: ['languages', 'interests'],
  native_language: 'fr',
  target_language: 'ja',
  target_level: 'A2',
  interest_ids: [],
  display_name: null,
  bio: null,
  has_avatar: false,
}

const CATALOG = [
  {
    category: 'Jeux vidéo',
    interests: [
      { id: 1, slug: 'a', label: 'RPG', label_en: 'RPG', emoji: '🗡️', category: 'Jeux vidéo', sort_order: 1 },
      { id: 2, slug: 'b', label: 'FPS', label_en: 'FPS', emoji: '🎯', category: 'Jeux vidéo', sort_order: 2 },
      { id: 3, slug: 'c', label: 'Coop', label_en: 'Coop', emoji: '🤝', category: 'Jeux vidéo', sort_order: 3 },
      { id: 4, slug: 'd', label: 'Rétro', label_en: 'Retro', emoji: '🕹️', category: 'Jeux vidéo', sort_order: 4 },
    ],
  },
]

beforeEach(() => {
  vi.clearAllMocks()
  apiMock.onboardingState.mockResolvedValue(STATE)
  apiMock.interests.mockResolvedValue(CATALOG)
  apiMock.setLanguages.mockResolvedValue({ ...STATE, step: 2 })
  apiMock.setInterests.mockResolvedValue({ ...STATE, step: 3, interest_ids: [1, 2, 3] })
  apiMock.messages.mockResolvedValue({ items: [], next_cursor: null })
  apiMock.markRead.mockResolvedValue({ unread_count: 0 })
  apiMock.complete.mockResolvedValue({ discoverable: true })
})

describe('Wizard', () => {
  it('affiche la progression 1/3 et désactive Continuer si les langues sont identiques', async () => {
    render(
      <MemoryRouter>
        <WizardPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('1/3')).toBeInTheDocument()
    const select = screen.getAllByRole('combobox')[1] as HTMLSelectElement
    await userEvent.selectOptions(select, 'fr')
    expect(screen.getByRole('button', { name: 'Continuer' })).toBeDisabled()
  })

  it('compte les intérêts et bloque sous 3', async () => {
    apiMock.onboardingState.mockResolvedValue({ ...STATE, step: 2 })
    render(
      <MemoryRouter>
        <WizardPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('0/12 — minimum 3 pour rencontrer quelqu\'un.')).toBeInTheDocument()
    const rpg = screen.getByRole('button', { name: /RPG/ })
    const fps = screen.getByRole('button', { name: /FPS/ })
    await userEvent.click(rpg)
    await userEvent.click(fps)
    expect(screen.getByRole('button', { name: 'Continuer' })).toBeDisabled()

    for (const label of [/Coop/, /Rétro/]) {
      await userEvent.click(screen.getByRole('button', { name: label }))
    }
    expect(screen.getByRole('button', { name: 'Continuer' })).toBeEnabled()
  })
})

const CANDIDATE = {
  user_id: 'u-1',
  display_name: 'Yuki',
  birth_year: 1994,
  bio: 'Bonjour',
  avatar_key: null,
  native_language: 'ja',
  target_language: 'fr',
  target_level: 'A1',
  score: 100,
  common_interest_ids: [1, 2, 3],
}

describe('Découverte', () => {
  it('un like appelle swipe une seule fois puis passe au profil suivant', async () => {
    apiMock.feed.mockResolvedValue({
      items: [CANDIDATE, { ...CANDIDATE, user_id: 'u-2', display_name: 'Kenji' }],
      next_offset: null,
      quota_reached: false,
    })
    apiMock.swipe.mockResolvedValue({ direction: 'like', match: null })

    render(
      <MemoryRouter>
        <DiscoverPage />
      </MemoryRouter>,
    )

    await userEvent.click(await screen.findByRole('button', { name: 'J\'aime' }))

    expect(apiMock.swipe).toHaveBeenCalledTimes(1)
    expect(apiMock.swipe).toHaveBeenCalledWith('u-1', 'like')
    expect(await screen.findByRole('heading', { name: 'Kenji' })).toBeInTheDocument()
  })

  it('la flèche droite déclenche un like', async () => {
    apiMock.feed.mockResolvedValue({ items: [CANDIDATE], next_offset: null, quota_reached: false })
    apiMock.swipe.mockResolvedValue({ direction: 'like', match: null })

    render(
      <MemoryRouter>
        <DiscoverPage />
      </MemoryRouter>,
    )
    await screen.findByRole('heading', { name: 'Yuki' })
    await userEvent.keyboard('{ArrowRight}')

    await waitFor(() => expect(apiMock.swipe).toHaveBeenCalledWith('u-1', 'like'))
  })

  it('affiche un état explicite quand le quota est atteint', async () => {
    apiMock.feed.mockResolvedValue({ items: [], next_offset: null, quota_reached: true })

    render(
      <MemoryRouter>
        <DiscoverPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText(/Plus de profils pour aujourd'hui/)).toBeInTheDocument()
  })
})

describe('Boîte de réception', () => {
  it('affiche le badge de non-lus et le dernier message', async () => {
    apiMock.conversations.mockResolvedValue({
      items: [
        {
          id: 'm-1',
          status: 'active',
          affinity_score: 90,
          other_user_id: 'u-1',
          display_name: 'Yuki',
          avatar_key: null,
          languages: 'ja → fr',
          last_message: 'bonjour',
          last_message_at: null,
          unread_count: 2,
        },
      ],
    })

    render(
      <MemoryRouter>
        <InboxPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Yuki')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('bonjour')).toBeInTheDocument()
  })
})

describe('Fil de discussion', () => {
  const MESSAGE = {
    id: 'msg-1',
    sender_id: 'u-1',
    body: 'bonjour je suis ravi',
    body_rendered: 'bonjour je suis ravi',
    body_lang: 'fr',
    created_at: new Date().toISOString(),
    edited_at: null,
    deleted_at: null,
    corrections: [],
  }

  function renderChat() {
    return render(
      <MemoryRouter initialEntries={['/messages/m-1']}>
        <Routes>
          <Route path="/messages/:matchId" element={<ChatPage />} />
        </Routes>
      </MemoryRouter>,
    )
  }

  it('affiche les icebreakers et les insère dans la zone de saisie', async () => {
    apiMock.match.mockResolvedValue({
      id: 'm-1',
      status: 'active',
      affinity_score: 100,
      other: {
        user_id: 'u-1',
        display_name: 'Yuki',
        avatar_key: null,
        bio: null,
        birth_year: 1994,
        native_language: 'ja',
        target_language: 'fr',
        target_level: 'A1',
      },
      icebreakers: [
        { position: 1, interest_slug: 'jeux-rpg', question_fr: 'À quel jeu joues-tu ?', question_en: '' },
        { position: 2, interest_slug: 'cuisine', question_fr: 'Ton plat réconfort ?', question_en: '' },
        { position: 3, interest_slug: 'voyage', question_fr: 'Ton plus beau voyage ?', question_en: '' },
      ],
    })
    apiMock.messages.mockResolvedValue({ items: [MESSAGE], next_cursor: null })

    renderChat()

    // La question est affichée en texte ; c'est le bouton « Utiliser » qui l'insère.
    expect(await screen.findByText('À quel jeu joues-tu ?')).toBeInTheDocument()
    const [useFirst] = screen.getAllByRole('button', { name: 'Utiliser' })
    if (!useFirst) throw new Error('bouton Utiliser introuvable')
    await userEvent.click(useFirst)

    expect(screen.getByPlaceholderText('Écrire un message…')).toHaveValue('À quel jeu joues-tu ?')
  })

  it('affiche la traduction à la demande avec le moteur utilisé', async () => {
    apiMock.match.mockResolvedValue({
      id: 'm-1', status: 'active', affinity_score: 100, other: null, icebreakers: [],
    })
    apiMock.messages.mockResolvedValue({ items: [MESSAGE], next_cursor: null })
    apiMock.translate.mockResolvedValue({ translated: 'こんにちは', provider: 'libretranslate', cached: false })

    renderChat()
    await userEvent.click(await screen.findByText('Traduire'))

    expect(await screen.findByText('こんにちは (libretranslate)')).toBeInTheDocument()
  })

  it('affiche le furigana en ruby/rt', async () => {
    apiMock.match.mockResolvedValue({
      id: 'm-1', status: 'active', affinity_score: 100, other: null, icebreakers: [],
    })
    apiMock.messages.mockResolvedValue({
      items: [{ ...MESSAGE, body: '私は学生です', body_rendered: '私は学生です' }],
      next_cursor: null,
    })
    apiMock.readingAid.mockResolvedValue({
      engine: 'fugashi',
      tokens: [
        { surface: '私', reading: 'わたし', romaji: 'watashi', start: 0, end: 1 },
        { surface: 'は', reading: 'は', romaji: 'ha', start: 1, end: 2 },
      ],
    })

    renderChat()
    await userEvent.click(await screen.findByText('Furigana'))

    const ruby = await screen.findByText('私')
    expect(ruby.tagName.toLowerCase()).toBe('ruby')
    expect(screen.getByText('watashi')).toBeInTheDocument()
  })

  it('le mode mot à mot ouvre une aide lexicale au clic sur un mot', async () => {
    apiMock.match.mockResolvedValue({
      id: 'm-1',
      status: 'active',
      affinity_score: 100,
      icebreakers: [],
      other: {
        user_id: 'u-1',
        display_name: 'Yuki',
        avatar_key: null,
        bio: null,
        birth_year: 1994,
        native_language: 'fr',
        target_language: 'ja',
        target_level: 'A2',
      },
    })
    apiMock.messages.mockResolvedValue({
      items: [{ ...MESSAGE, body: 'le marché', body_rendered: 'le marché' }],
      next_cursor: null,
    })
    apiMock.lexicon.mockResolvedValue({
      word: 'marché',
      source: 'wiktionnaire',
      reading: null,
      senses: [{ part_of_speech: 'commerce', definition: 'Lieu public de vente.' }],
    })

    renderChat()
    await userEvent.click(await screen.findByRole('button', { name: 'Mot à mot' }))
    await userEvent.click(await screen.findByRole('button', { name: 'marché' }))

    expect(apiMock.lexicon).toHaveBeenCalledWith('marché', 'fr')
    expect(await screen.findByText(/Lieu public de vente/)).toBeInTheDocument()
    expect(screen.getByText('Source : Wiktionnaire francophone')).toBeInTheDocument()
  })

  it('propose Accepter / Refuser sur une correction en attente', async () => {
    apiMock.match.mockResolvedValue({
      id: 'm-1', status: 'active', affinity_score: 100, other: null, icebreakers: [],
    })
    apiMock.messages.mockResolvedValue({
      items: [
        {
          ...MESSAGE,
          corrections: [
            {
              id: 'c-1',
              message_id: 'msg-1',
              corrector_id: 'u-2',
              start_offset: 16,
              end_offset: 20,
              original_text: 'ravi',
              replacement: 'ravie',
              explanation: null,
              status: 'pending',
            },
          ],
        },
      ],
      next_cursor: null,
    })
    apiMock.acceptCorrection.mockResolvedValue({ status: 'accepted' })

    renderChat()
    await userEvent.click(await screen.findByRole('button', { name: 'Accepter' }))

    expect(apiMock.acceptCorrection).toHaveBeenCalledWith('c-1')
  })
})
