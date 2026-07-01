import { useCallback, useEffect, useState } from 'react'
import { checkHealth, reviewCode } from './api/client'
import { CodeInput } from './components/CodeInput'
import { ReviewPanel } from './components/ReviewPanel'
import type { CompareReviewResponse } from './types'

const DEFAULT_CODE = `def divide(a, b):
    return a / b`

export default function App() {
  const [code, setCode] = useState(DEFAULT_CODE)
  const [language, setLanguage] = useState('python')
  const [userName, setUserName] = useState(() => {
    const params = new URLSearchParams(window.location.search)
    return params.get('user') || localStorage.getItem('cra_user_name') || ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<CompareReviewResponse | null>(null)
  const [apiMode, setApiMode] = useState<string>('checking...')
  const [oauthEnabled, setOauthEnabled] = useState(false)

  useEffect(() => {
    checkHealth()
      .then((h) => {
        setApiMode(h.inference_mode)
        setOauthEnabled(h.oauth_enabled)
      })
      .catch(() => setApiMode('offline'))
  }, [])

  const handleReview = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await reviewCode({
        code,
        language,
        user_name: userName.trim() || undefined,
      })
      if (userName.trim()) localStorage.setItem('cra_user_name', userName.trim())
      setResult(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Review failed')
    } finally {
      setLoading(false)
    }
  }, [code, language, userName])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <header className="border-b border-slate-800/80 bg-slate-950/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Code Review <span className="text-emerald-400">Assistant</span>
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Fine-tuned Mistral 7B vs base model — side by side
            </p>
          </div>
          <div className="flex items-center gap-4">
            {oauthEnabled && (
              <a href="/api/auth/github" className="text-xs text-slate-400 hover:text-emerald-400">
                Sign in with GitHub
              </a>
            )}
            <a href="/admin" className="text-xs text-slate-400 hover:text-emerald-400">Admin</a>
            <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">mode:</span>
            <span className="text-xs px-2 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-300 font-mono" data-testid="inference-mode">
              {apiMode}
            </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        <CodeInput
          code={code}
          language={language}
          userName={userName}
          onCodeChange={setCode}
          onLanguageChange={setLanguage}
          onUserNameChange={setUserName}
          onSubmit={handleReview}
          loading={loading}
        />

        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
            <span className="block text-xs text-red-400/70 mt-1">
              Make sure the backend is running: <code className="font-mono">uvicorn main:app --reload</code>
            </span>
          </div>
        )}

        <section>
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-semibold text-white">Before vs After</h2>
            <span className="text-xs text-slate-500">Base Mistral 7B ← → Fine-tuned LoRA</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ReviewPanel
              title="Base Mistral 7B"
              subtitle="Generic, vague feedback"
              comments={result?.base_model.comments ?? []}
              latencyMs={result?.base_model.latency_ms}
              accent="slate"
              loading={loading}
              testId="base-panel"
            />
            <ReviewPanel
              title="Specialized Model"
              subtitle="CodeReviewer / fine-tuned LoRA"
              comments={result?.finetuned_model.comments ?? []}
              latencyMs={result?.finetuned_model.latency_ms}
              accent="emerald"
              loading={loading}
              testId="finetuned-panel"
            />
          </div>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">How it works</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
            {[
              { step: '1', label: 'Dataset', desc: '167K real PR reviews' },
              { step: '2', label: 'Fine-tune', desc: 'QLoRA on Mistral 7B' },
              { step: '3', label: 'Evaluate', desc: 'BLEU-4 + type accuracy' },
              { step: '4', label: 'Deploy', desc: 'FastAPI + React UI' },
            ].map((item) => (
              <div key={item.step} className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/40">
                <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 text-sm font-bold flex items-center justify-center mx-auto mb-2">
                  {item.step}
                </div>
                <p className="text-sm font-medium text-white">{item.label}</p>
                <p className="text-xs text-slate-500 mt-1">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-800 mt-12 py-6 text-center text-xs text-slate-600">
        Code Review Assistant — LoRA fine-tuning on real code review data
      </footer>
    </div>
  )
}
