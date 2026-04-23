import { Outlet, NavLink } from 'react-router-dom'
import { FlaskConical, Plus, List } from 'lucide-react'

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-9 h-9 bg-brand-600 rounded-lg">
                <FlaskConical className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="font-bold text-gray-900 text-sm leading-none block">AI Protocol Generator</span>
                <span className="text-xs text-gray-400 leading-none">Qwen3.5-122B · GCP/ICH · FOR REVIEW ONLY</span>
              </div>
            </div>
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
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <p className="text-xs text-gray-400 text-center">
            AI Protocol Generator v0.1.0 · FOR RESEARCH USE ONLY — NOT FOR CLINICAL USE ·
            Powered by InHouse/Qwen3.5-122B via internal AI Gateway
          </p>
        </div>
      </footer>
    </div>
  )
}
