import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { App } from './App'

describe('App', () => {
  it('affiche la proposition de valeur', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { name: /échangez avec des personnes/i }),
    ).toBeInTheDocument()
    expect(screen.getByText(/correspondance asynchrone/i)).toBeInTheDocument()
  })
})
