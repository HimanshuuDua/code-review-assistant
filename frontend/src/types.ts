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
}
