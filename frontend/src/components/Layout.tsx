import { Outlet, NavLink, Link } from 'react-router-dom'
import { Sparkles, Plus, List, LogOut, Shield, User, ScrollText } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const ROLE_BADGE: Record<string, { label: string; cls: string }> = {
  admin:    { label: 'Admin',    cls: 'bg-red-100 text-red-700' },
  employee: { label: 'Employee', cls: 'bg-sky-100 text-sky-700' },
  auditor:  { label: 'Auditor',  cls: 'bg-gray-100 text-gray-600' },
}

export default function Layout() {
  const { user, logout } = useAuth()
  const badge = user ? ROLE_BADGE[user.role] : null

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/protocols" className="flex items-center gap-3 group">
              {/* Gradient orb logo */}
              <div
                className="flex items-center justify-center w-10 h-10 rounded-xl flex-shrink-0 group-hover:opacity-90 transition-opacity"
                style={{ background: 'linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #22d3ee 100%)' }}
              >
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div className="leading-none">
                <span className="font-bold text-gray-900 text-lg leading-tight block tracking-tight group-hover:text-brand-700 transition-colors">Synthia</span>
                <span className="text-xs text-gray-400 leading-none">AI Protocol Generator</span>
              </div>
            </Link>

            <div className="flex items-center gap-3">
              <nav className="flex items-center gap-1">
                <NavLink
                  to="/protocols"
                  end
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-100'
                    }`
                  }
                >
                  <List className="w-4 h-4" />
                  Протоколы
                </NavLink>
                {user?.role !== 'auditor' && (
                  <NavLink
                    to="/protocols/new"
                    className={({ isActive }) =>
                      `flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        isActive ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-100'
                      }`
                    }
                  >
                    <Plus className="w-4 h-4" />
                    Новый протокол
                  </NavLink>
                )}
                <NavLink
                  to="/audit"
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-100'
                    }`
                  }
                >
                  <ScrollText className="w-4 h-4" />
                  Аудит
                </NavLink>
              </nav>

              {user && (
                <div className="flex items-center gap-2 pl-3 border-l border-gray-200">
                  <User className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-700 font-medium">{user.username}</span>
                  {badge && (
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badge.cls}`}>
                      {badge.label}
                    </span>
                  )}
                  <button
                    onClick={logout}
                    title="Выйти"
                    className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <p className="text-xs text-gray-400">
              Synthia v1.0.0 · FOR RESEARCH USE ONLY — NOT FOR CLINICAL USE ·
              Powered by InHouse/Qwen3.5-122B via internal AI Gateway
            </p>
            <a
              href="https://grls.rosminzdrav.ru/CIPermission.aspx"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-700"
            >
              <Shield className="w-3 h-3" />
              Федеральный реестр КИ Минздрава РФ
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
