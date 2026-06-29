export type CommentType =
  | 'bug'
  | 'security'
  | 'performance'
  | 'style'
  | 'suggestion'
  | 'refactor'
  | 'question'

export type Severity = 'high' | 'medium' | 'low'

export interface ReviewComment {
  type: CommentType
  severity: Severity
  message: string
  line?: number | null
}

export interface ModelReviewResult {
  model_name: string
  comments: ReviewComment[]
  raw_response: string
  latency_ms?: number | null
}

export interface CompareReviewResponse {
  base_model: ModelReviewResult
  finetuned_model: ModelReviewResult
}

export interface ReviewRequest {
  code: string
  language: string
  context?: string
  user_name?: string
}

export interface ReviewHistoryItem {
  id: string
  user_name: string
  client_ip: string | null
  language: string
  code_preview: string
  code: string
  context: string | null
  issue_types: string[]
  finetuned_comment_count: number
  base_comments_json: string
  finetuned_comments_json: string
  inference_mode: string
  created_at: string
}

export interface ReviewHistoryResponse {
  items: ReviewHistoryItem[]
  total: number
  limit: number
  offset: number
}

export interface ReviewStats {
  total_reviews: number
  unique_users: number
}
