import { useState, FormEvent } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Sparkles, LogIn, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const ROLE_LABELS: Record<string, string> = {
  admin: 'Admin — полный доступ',
  employee: 'Employee — полный доступ',
  auditor: 'Auditor — только чтение',
}

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string })?.from || '/protocols'

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password.trim()) {
      setError('Введите логин и пароль')
      return
    }
    setLoading(true)
    setError(null)
    try {
      await login(username.trim(), password)
      navigate(from, { replace: true })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div
            className="flex items-center justify-center w-14 h-14 rounded-2xl mb-4 shadow-lg"
            style={{ background: 'linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #22d3ee 100%)' }}
          >
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Synthia</h1>
          <p className="text-sm text-gray-500 mt-1">AI Protocol Generator</p>
        </div>

        {/* Card */}
        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-5">Вход в систему</h2>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="form-label">Логин</label>
              <input
                className="form-input"
                autoComplete="username"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="admin / employee / auditor"
                disabled={loading}
              />
            </div>

            <div>
              <label className="form-label">Пароль</label>
              <div className="relative">
                <input
                  className="form-input pr-10"
                  type={showPw ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPw(v => !v)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  tabIndex={-1}
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center"
            >
              <LogIn className="w-4 h-4" />
              {loading ? 'Вход...' : 'Войти'}
            </button>
          </form>
        </div>

        {/* Demo users hint */}
        <div className="mt-4 card p-4">
          <p className="text-xs font-medium text-gray-500 mb-2">Демо-пользователи</p>
          <div className="space-y-1.5">
            {[
              { u: 'admin',    p: 'admin123',    r: 'admin' },
              { u: 'employee', p: 'employee123', r: 'employee' },
              { u: 'auditor',  p: 'auditor123',  r: 'auditor' },
            ].map(({ u, p, r }) => (
              <button
                key={u}
                type="button"
                onClick={() => { setUsername(u); setPassword(p) }}
                className="w-full flex items-center justify-between text-left px-2 py-1.5 rounded hover:bg-gray-50 transition-colors"
              >
                <span className="text-sm font-mono text-gray-700">{u} / {p}</span>
                <span className="text-xs text-gray-400">{ROLE_LABELS[r]}</span>
              </button>
            ))}
          </div>
        </div>

        <p className="text-xs text-gray-400 text-center mt-4">
          FOR RESEARCH USE ONLY — NOT FOR CLINICAL USE
        </p>
      </div>
    </div>
  )
}
