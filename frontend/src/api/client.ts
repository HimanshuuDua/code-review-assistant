import type { CompareReviewResponse, ReviewRequest } from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

export async function reviewCode(request: ReviewRequest): Promise<CompareReviewResponse> {
  const response = await fetch(`${API_BASE}/api/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Request failed (${response.status})`)
  }

  return response.json()
}

export async function checkHealth(): Promise<{ status: string; inference_mode: string }> {
  const response = await fetch(`${API_BASE}/api/health`)
  if (!response.ok) throw new Error('API unavailable')
  return response.json()
}
