import { useCallback, useEffect, useState } from 'react'
import { fetchReviewHistory, fetchReviewStats } from '../api/client'
import type { ReviewHistoryItem } from '../types'

const ADMIN_KEY_STORAGE = 'cra_admin_key'

export default function AdminPage() {
  const [adminKey, setAdminKey] = useState(() => sessionStorage.getItem(ADMIN_KEY_STORAGE) ?? '')
  const [inputKey, setInputKey] = useState(adminKey)
  const [items, setItems] = useState<ReviewHistoryItem[]>([])
  const [total, setTotal] = useState(0)
  const [stats, setStats] = useState<{ total_reviews: number; unique_users: number } | null>(null)
  const [selected, setSelected] = useState<ReviewHistoryItem | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async (key: string) => {
    if (!key) return
    setLoading(true)
    setError(null)
    try {
      const [history, reviewStats] = await Promise.all([
        fetchReviewHistory(key),
        fetchReviewStats(key),
      ])
      setItems(history.items)
      setTotal(history.total)
      setStats(reviewStats)
      sessionStorage.setItem(ADMIN_KEY_STORAGE, key)
      setAdminKey(key)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load')
      setItems([])
      setStats(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (adminKey) load(adminKey)
  }, [adminKey, load])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 px-6 py-5 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Review History</h1>
          <p className="text-sm text-slate-400">Who reviewed what and what issues were found</p>
        </div>
        <a href="/" className="text-sm text-emerald-400 hover:text-emerald-300">← Back to app</a>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="text-xs text-slate-500 block mb-1">Admin API Key</label>
            <input
              type="password"
              value={inputKey}
              onChange={(e) => setInputKey(e.target.value)}
              placeholder="Enter ADMIN_API_KEY"
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm w-72"
            />
          </div>
          <button
            type="button"
            onClick={() => load(inputKey)}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm font-medium"
          >
            Load
          </button>
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total reviews" value={stats.total_reviews} />
            <StatCard label="Unique users" value={stats.unique_users} />
            <StatCard label="Showing" value={items.length} />
            <StatCard label="Total stored" value={total} />
          </div>
        )}

        {loading ? (
          <p className="text-slate-500">Loading...</p>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-xl border border-slate-800 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-slate-900 text-slate-400 text-left">
                  <tr>
                    <th className="px-4 py-3">User</th>
                    <th className="px-4 py-3">Lang</th>
                    <th className="px-4 py-3">Issues</th>
                    <th className="px-4 py-3">When</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr
                      key={item.id}
                      onClick={() => setSelected(item)}
                      className={`border-t border-slate-800 cursor-pointer hover:bg-slate-900/60 ${selected?.id === item.id ? 'bg-slate-900/80' : ''}`}
                    >
                      <td className="px-4 py-3 font-medium">{item.user_name}</td>
                      <td className="px-4 py-3 text-slate-400">{item.language}</td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {item.issue_types.map((t) => (
                            <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700">
                              {t}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-500 text-xs">
                        {new Date(item.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                  {items.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                        No reviews yet. Submit code on the main page.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="rounded-xl border border-slate-800 p-5 bg-slate-900/40 min-h-[320px]">
              {selected ? (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-white">{selected.user_name}</h3>
                    <p className="text-xs text-slate-500">
                      {selected.language} · {selected.client_ip ?? 'no IP'} · {new Date(selected.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Code reviewed</p>
                    <pre className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-emerald-100 overflow-x-auto">
                      {selected.code}
                    </pre>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Fine-tuned findings ({selected.finetuned_comment_count})</p>
                    <div className="space-y-2">
                      {JSON.parse(selected.finetuned_comments_json).map((c: { type: string; severity: string; message: string }, i: number) => (
                        <div key={i} className="rounded-lg border border-slate-700 p-3 text-sm">
                          <span className="text-xs uppercase text-red-400 mr-2">{c.type}</span>
                          <span className="text-xs text-amber-400">{c.severity}</span>
                          <p className="mt-1 text-slate-200">{c.message}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-slate-500 text-sm">Select a review to see details</p>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-2xl font-bold text-white mt-1">{value}</p>
    </div>
  )
}
