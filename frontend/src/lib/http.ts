/**
 * Client HTTP minimal.
 *
 * Toutes les requêtes de l'application passent par ici : jamais de `fetch` direct dans un
 * composant (design D-12). Les erreurs sont normalisées au format RFC 9457 renvoyé par
 * l'API (`application/problem+json`).
 */

export interface Problem {
  type: string
  title: string
  status: number
  detail?: string
  errors?: Array<{ field: string; code: string; message?: string }>
}

export class ApiError extends Error {
  readonly problem: Problem

  constructor(problem: Problem) {
    super(problem.detail ?? problem.title)
    this.name = 'ApiError'
    this.problem = problem
  }
}

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api/v1'

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...init.headers,
    },
    credentials: 'include',
  })

  if (!response.ok) {
    const problem = (await response.json().catch(() => ({
      type: 'about:blank',
      title: response.statusText,
      status: response.status,
    }))) as Problem
    throw new ApiError(problem)
  }

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}
