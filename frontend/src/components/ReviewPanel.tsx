import type { ReviewComment, Severity } from '../types'

const SEVERITY_STYLES: Record<Severity, string> = {
  high: 'bg-red-500/15 text-red-300 border-red-500/30',
  medium: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  low: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
}

const TYPE_STYLES: Record<string, string> = {
  bug: 'text-red-400',
  security: 'text-orange-400',
  performance: 'text-yellow-400',
  style: 'text-purple-400',
  suggestion: 'text-blue-400',
  refactor: 'text-teal-400',
  question: 'text-gray-400',
}

interface ReviewPanelProps {
  title: string
  subtitle: string
  comments: ReviewComment[]
  latencyMs?: number | null
  accent: 'slate' | 'emerald'
  loading?: boolean
  testId?: string
}

export function ReviewPanel({
  title,
  subtitle,
  comments,
  latencyMs,
  accent,
  loading,
  testId,
}: ReviewPanelProps) {
  const borderColor = accent === 'emerald' ? 'border-emerald-500/40' : 'border-slate-600'
  const headerBg = accent === 'emerald' ? 'bg-emerald-500/10' : 'bg-slate-800/80'

  return (
    <div className={`flex flex-col rounded-xl border ${borderColor} bg-slate-900/60 overflow-hidden`} data-testid={testId}>
      <div className={`px-5 py-4 border-b border-slate-700/60 ${headerBg}`}>
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-white">{title}</h3>
            <p className="text-sm text-slate-400 mt-0.5">{subtitle}</p>
          </div>
          {latencyMs != null && (
            <span className="text-xs text-slate-500 shrink-0">{Math.round(latencyMs)}ms</span>
          )}
        </div>
      </div>

      <div className="flex-1 p-4 space-y-3 min-h-[280px]">
        {loading ? (
          <div className="flex items-center justify-center h-full text-slate-500">
            <div className="animate-pulse text-center">
              <div className="w-8 h-8 border-2 border-slate-600 border-t-emerald-400 rounded-full animate-spin mx-auto mb-3" />
              <p className="text-sm">Generating review...</p>
            </div>
          </div>
        ) : comments.length === 0 ? (
          <p className="text-slate-500 text-sm text-center py-8">No comments yet</p>
        ) : (
          comments.map((comment, i) => (
            <div
              key={i}
              className="rounded-lg border border-slate-700/60 bg-slate-800/40 p-4 hover:border-slate-600 transition-colors"
            >
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className={`text-xs font-semibold uppercase tracking-wide ${TYPE_STYLES[comment.type] ?? 'text-slate-400'}`}>
                  {comment.type}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full border ${SEVERITY_STYLES[comment.severity]}`}>
                  {comment.severity}
                </span>
                {comment.line != null && (
                  <span className="text-xs text-slate-500">line {comment.line}</span>
                )}
              </div>
              <p className="text-sm text-slate-200 leading-relaxed">{comment.message}</p>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
