import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { App } from './App'

describe('App', () => {
  it('affiche la proposition de valeur sur la page d\'accueil', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )

    expect(
      screen.getByRole('heading', { name: /échangez avec des personnes/i }),
    ).toBeInTheDocument()
    expect(screen.getByText(/deux humains qui s'apprennent mutuellement/i)).toBeInTheDocument()
  })
})
