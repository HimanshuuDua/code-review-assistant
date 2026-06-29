const EXAMPLES = [
  {
    label: 'Division by zero',
    language: 'python',
    code: `def divide(a, b):\n    return a / b`,
  },
  {
    label: 'SQL injection',
    language: 'python',
    code: `def get_user(username):\n    query = "SELECT * FROM users WHERE name = '" + username + "'"\n    return db.execute(query)`,
  },
  {
    label: 'Hardcoded secret',
    language: 'python',
    code: `API_KEY = "sk-live-abc123xyz"\n\ndef connect():\n    return requests.get(url, headers={"Authorization": API_KEY})`,
  },
]

interface CodeInputProps {
  code: string
  language: string
  onCodeChange: (code: string) => void
  onLanguageChange: (language: string) => void
  onSubmit: () => void
  loading: boolean
}

export function CodeInput({
  code,
  language,
  onCodeChange,
  onLanguageChange,
  onSubmit,
  loading,
}: CodeInputProps) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/60 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/60 bg-slate-800/50">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-slate-300">Code to review</span>
          <select
            value={language}
            onChange={(e) => onLanguageChange(e.target.value)}
            className="text-xs bg-slate-700 border border-slate-600 rounded-md px-2 py-1 text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            {['python', 'javascript', 'typescript', 'java', 'go', 'rust', 'cpp'].map((lang) => (
              <option key={lang} value={lang}>
                {lang}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          onClick={onSubmit}
          disabled={loading || !code.trim()}
          data-testid="review-button"
          className="px-4 py-1.5 text-sm font-medium rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Reviewing...' : 'Review Code'}
        </button>
      </div>

      <textarea
        value={code}
        onChange={(e) => onCodeChange(e.target.value)}
        placeholder="Paste your code snippet here..."
        spellCheck={false}
        data-testid="code-textarea"
        className="w-full h-52 p-4 bg-slate-950 text-emerald-100 font-mono text-sm leading-relaxed resize-y focus:outline-none placeholder:text-slate-600"
      />

      <div className="px-4 py-3 border-t border-slate-700/60 bg-slate-800/30">
        <p className="text-xs text-slate-500 mb-2">Try an example:</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex.label}
              type="button"
              onClick={() => {
                onCodeChange(ex.code)
                onLanguageChange(ex.language)
              }}
              className="text-xs px-3 py-1 rounded-full border border-slate-600 text-slate-400 hover:border-emerald-500/50 hover:text-emerald-400 transition-colors"
            >
              {ex.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
