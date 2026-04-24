import { useEffect, useState, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  Plus, FlaskConical, Clock, ChevronRight,
  Tag, X, Search, SlidersHorizontal, ChevronDown,
} from 'lucide-react'
import { api, type ProtocolListItem } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import StatusBadge from '../components/StatusBadge'
import TagBadge from '../components/TagBadge'
import ErrorAlert from '../components/ErrorAlert'
import Spinner from '../components/Spinner'

const PHASE_OPTIONS = [
  { value: '', label: 'Все фазы' },
  { value: 'I',   label: 'Фаза I' },
  { value: 'II',  label: 'Фаза II' },
  { value: 'III', label: 'Фаза III' },
  { value: 'IV',  label: 'Фаза IV' },
]

const STATUS_OPTIONS = [
  { value: '', label: 'Все статусы' },
  { value: 'draft',    label: 'Черновик' },
  { value: 'generated', label: 'Сгенерирован' },
  { value: 'approved', label: 'Одобрен' },
  { value: 'archived', label: 'В архиве' },
]

const AREA_OPTIONS = [
  '', 'Онкология', 'Кардиология', 'Неврология', 'Эндокринология',
  'Пульмонология', 'Ревматология', 'Гастроэнтерология', 'Иммунология', 'Другое',
]

const PHASE_LABELS: Record<string, string> = {
  I: 'Фаза I', II: 'Фаза II', III: 'Фаза III', IV: 'Фаза IV',
  phase_1: 'Фаза I', phase_2: 'Фаза II', phase_3: 'Фаза III', phase_4: 'Фаза IV',
}

export default function ProtocolListPage() {
  const { user } = useAuth()

  // Data
  const [protocols, setProtocols] = useState<ProtocolListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [allTags, setAllTags] = useState<string[]>([])

  // Search state
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const searchRef = useRef<HTMLDivElement>(null)

  // Filters
  const [showFilters, setShowFilters] = useState(false)
  const [phase, setPhase] = useState('')
  const [status, setStatus] = useState('')
  const [area, setArea] = useState('')
  const [tagFilter, setTagFilter] = useState<string | null>(null)

  const activeFilterCount = [phase, status, area, tagFilter].filter(Boolean).length

  // Load protocols (server-side search + filters)
  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.listProtocols({
        limit: 100,
        search: searchQuery || undefined,
        phase: phase || undefined,
        status: status || undefined,
        therapeutic_area: area || undefined,
        tag: tagFilter ?? undefined,
      })
      setProtocols(data)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [searchQuery, phase, status, area, tagFilter])

  useEffect(() => { load() }, [load])

  useEffect(() => { api.getAllTags().then(setAllTags).catch(() => {}) }, [])

  // Debounce search input → suggestions
  useEffect(() => {
    if (searchInput.length < 2) { setSuggestions([]); return }
    const timer = setTimeout(async () => {
      try {
        const data = await api.listProtocols({ limit: 50, search: searchInput })
        const titles = data.map(p => p.title).slice(0, 8)
        setSuggestions(titles)
      } catch { setSuggestions([]) }
    }, 250)
    return () => clearTimeout(timer)
  }, [searchInput])

  // Close suggestions on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSearchSubmit = (value: string) => {
    setSearchQuery(value)
    setSearchInput(value)
    setShowSuggestions(false)
  }

  const handleTagClick = (tag: string) => {
    setTagFilter(prev => prev === tag ? null : tag)
  }

  const resetFilters = () => {
    setPhase(''); setStatus(''); setArea(''); setTagFilter(null)
    setSearchQuery(''); setSearchInput('')
  }

  const fmt = (iso: string) =>
    new Date(iso).toLocaleString('ru', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Протоколы</h1>
          <p className="text-sm text-gray-500 mt-0.5">Клинические протоколы, сгенерированные AI</p>
        </div>
        {user?.role !== 'auditor' && (
          <Link to="/protocols/new" className="btn-primary">
            <Plus className="w-4 h-4" />
            Новый протокол
          </Link>
        )}
      </div>

      {error && <div className="mb-4"><ErrorAlert message={error} onClose={() => setError(null)} /></div>}

      {/* Search + filter bar */}
      <div className="mb-4 space-y-3">
        <div className="flex gap-2">
          {/* Search with autocomplete */}
          <div className="relative flex-1" ref={searchRef}>
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            <input
              type="text"
              placeholder="Поиск по названию или препарату..."
              value={searchInput}
              onChange={e => { setSearchInput(e.target.value); setShowSuggestions(true) }}
              onFocus={() => { if (suggestions.length) setShowSuggestions(true) }}
              onKeyDown={e => {
                if (e.key === 'Enter') handleSearchSubmit(searchInput)
                if (e.key === 'Escape') setShowSuggestions(false)
              }}
              className="form-input pl-9 pr-9"
            />
            {searchInput && (
              <button
                onClick={() => { setSearchInput(''); setSearchQuery(''); setShowSuggestions(false) }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
            {/* Autocomplete dropdown */}
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 overflow-hidden">
                {suggestions.map((title, i) => (
                  <button
                    key={i}
                    onMouseDown={e => { e.preventDefault(); handleSearchSubmit(title) }}
                    className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-brand-50 hover:text-brand-700 transition-colors flex items-center gap-2"
                  >
                    <Search className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                    <span className="truncate">{title}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Filter toggle */}
          <button
            onClick={() => setShowFilters(v => !v)}
            className={`btn-secondary flex items-center gap-2 relative ${showFilters ? 'bg-brand-50 border-brand-300 text-brand-700' : ''}`}
          >
            <SlidersHorizontal className="w-4 h-4" />
            Фильтры
            {activeFilterCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-brand-600 text-white rounded-full text-[10px] flex items-center justify-center font-bold">
                {activeFilterCount}
              </span>
            )}
            <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Filter panel */}
        {showFilters && (
          <div className="card p-4 flex flex-wrap gap-3 items-end">
            <div>
              <label className="form-label">Фаза исследования</label>
              <select className="form-input text-sm" value={phase} onChange={e => setPhase(e.target.value)}>
                {PHASE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div>
              <label className="form-label">Статус</label>
              <select className="form-input text-sm" value={status} onChange={e => setStatus(e.target.value)}>
                {STATUS_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div>
              <label className="form-label">Терапевтическая область</label>
              <select className="form-input text-sm" value={area} onChange={e => setArea(e.target.value)}>
                {AREA_OPTIONS.map(a => <option key={a} value={a}>{a || 'Все области'}</option>)}
              </select>
            </div>
            <div>
              <label className="form-label flex items-center gap-1">
                <Tag className="w-3.5 h-3.5" /> Тег
              </label>
              <select
                className="form-input text-sm"
                value={tagFilter ?? ''}
                onChange={e => setTagFilter(e.target.value || null)}
              >
                <option value="">Все теги</option>
                {allTags.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            {activeFilterCount > 0 && (
              <button onClick={resetFilters} className="btn-secondary text-sm flex items-center gap-1.5 self-end">
                <X className="w-3.5 h-3.5" /> Сбросить всё
              </button>
            )}
          </div>
        )}

        {/* Active chips */}
        {(tagFilter || searchQuery) && (
          <div className="flex flex-wrap items-center gap-2 text-sm">
            {searchQuery && (
              <span className="flex items-center gap-1 bg-brand-50 text-brand-700 border border-brand-200 rounded-full px-3 py-0.5 text-xs">
                <Search className="w-3 h-3" /> «{searchQuery}»
                <button onClick={() => { setSearchQuery(''); setSearchInput('') }} className="ml-1 hover:text-brand-900">
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
            {tagFilter && (
              <span className="flex items-center gap-1 text-xs text-gray-500">
                <Tag className="w-3 h-3" />
                <TagBadge tag={tagFilter} />
                <button onClick={() => setTagFilter(null)} className="text-gray-400 hover:text-gray-600">
                  <X className="w-3.5 h-3.5" />
                </button>
              </span>
            )}
          </div>
        )}
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex justify-center py-20"><Spinner size={32} /></div>
      ) : protocols.length === 0 ? (
        <EmptyState hasFilters={!!(searchQuery || phase || status || area || tagFilter)} onReset={resetFilters} />
      ) : (
        <>
          <p className="text-xs text-gray-400 mb-2 px-1">Найдено: {protocols.length}</p>
          <div className="card divide-y divide-gray-100">
            {protocols.map(p => (
              <Link
                key={p.id}
                to={`/protocols/${p.id}`}
                className="flex items-center gap-4 px-6 py-4 hover:bg-gray-50 transition-colors group cursor-pointer"
              >
                <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-brand-50 flex-shrink-0">
                  <FlaskConical className="w-5 h-5 text-brand-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-gray-900 truncate">{p.title}</span>
                    <StatusBadge status={p.status} />
                    <span className="badge bg-gray-100 text-gray-600">
                      {PHASE_LABELS[p.phase] ?? p.phase}
                    </span>
                    {(p.tags ?? []).map(tag => (
                      <TagBadge
                        key={tag} tag={tag}
                        onClick={e => { e.preventDefault(); handleTagClick(tag) }}
                      />
                    ))}
                  </div>
                  <div className="flex items-center gap-1 text-xs text-gray-400 mt-0.5">
                    <Clock className="w-3 h-3" />
                    {fmt(p.updated_at)}
                    <span className="mx-1">·</span>
                    <span className="font-medium text-gray-500 truncate max-w-[200px]" title={p.drug_name}>{p.drug_name}</span>
                    {p.therapeutic_area && (
                      <><span className="mx-1">·</span><span>{p.therapeutic_area}</span></>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-brand-600" />
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function EmptyState({ hasFilters, onReset }: { hasFilters: boolean; onReset: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="flex items-center justify-center w-16 h-16 bg-brand-50 rounded-2xl mb-4">
        <FlaskConical className="w-8 h-8 text-brand-600" />
      </div>
      {hasFilters ? (
        <>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Ничего не найдено</h3>
          <p className="text-gray-500 text-sm mb-6 max-w-sm">
            Попробуйте изменить критерии поиска или сбросить фильтры
          </p>
          <button onClick={onReset} className="btn-secondary">
            <X className="w-4 h-4" /> Сбросить фильтры
          </button>
        </>
      ) : (
        <>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Протоколов пока нет</h3>
          <p className="text-gray-500 text-sm mb-6 max-w-sm">
            Создайте первый клинический протокол — AI сгенерирует все разделы в соответствии с ICH E6 GCP.
          </p>
          <Link to="/protocols/new" className="btn-primary">
            <Plus className="w-4 h-4" /> Создать первый протокол
          </Link>
        </>
      )}
    </div>
  )
}
