import type { CompareReviewResponse, ReviewHistoryResponse, ReviewRequest, ReviewStats } from '../types'

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

export async function checkHealth(): Promise<{ status: string; inference_mode: string; storage_enabled: boolean; oauth_enabled: boolean }> {
  const response = await fetch(`${API_BASE}/api/health`)
  if (!response.ok) throw new Error('API unavailable')
  return response.json()
}

export async function fetchReviewHistory(
  adminKey: string,
  limit = 50,
  offset = 0,
): Promise<ReviewHistoryResponse> {
  const response = await fetch(`${API_BASE}/api/admin/reviews?limit=${limit}&offset=${offset}`, {
    headers: { 'X-Admin-Key': adminKey },
  })
  if (!response.ok) throw new Error(response.status === 401 ? 'Invalid admin key' : 'Failed to load history')
  return response.json()
}

export async function fetchReviewStats(adminKey: string): Promise<ReviewStats> {
  const response = await fetch(`${API_BASE}/api/admin/stats`, {
    headers: { 'X-Admin-Key': adminKey },
  })
  if (!response.ok) throw new Error('Failed to load stats')
  return response.json()
}
