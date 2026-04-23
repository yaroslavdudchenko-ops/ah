import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, FlaskConical, Clock, ChevronRight, Trash2 } from 'lucide-react'
import { api, type ProtocolListItem } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import Spinner from '../components/Spinner'
import ErrorAlert from '../components/ErrorAlert'

const PHASE_LABELS: Record<string, string> = {
  '1': 'Фаза I', '2': 'Фаза II', '3': 'Фаза III', '4': 'Фаза IV',
  phase_1: 'Фаза I', phase_2: 'Фаза II', phase_3: 'Фаза III',
}

export default function ProtocolListPage() {
  const [protocols, setProtocols] = useState<ProtocolListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)

  const load = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.listProtocols({ limit: 50 })
      setProtocols(data)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleDelete = async (id: string, title: string) => {
    if (!confirm(`Удалить протокол «${title}»?`)) return
    setDeleting(id)
    try {
      await api.deleteProtocol(id)
      setProtocols(prev => prev.filter(p => p.id !== id))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setDeleting(null)
    }
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
        <Link to="/protocols/new" className="btn-primary">
          <Plus className="w-4 h-4" />
          Новый протокол
        </Link>
      </div>

      {error && <div className="mb-4"><ErrorAlert message={error} onClose={() => setError(null)} /></div>}

      {loading ? (
        <div className="flex justify-center py-20">
          <Spinner size={32} />
        </div>
      ) : protocols.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="card divide-y divide-gray-100">
          {protocols.map(p => (
            <div key={p.id} className="flex items-center gap-4 px-6 py-4 hover:bg-gray-50 transition-colors group">
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
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-400 mt-0.5">
                  <Clock className="w-3 h-3" />
                  {fmt(p.updated_at)}
                  <span className="mx-1">·</span>
                  <span className="font-medium text-gray-500">{p.drug_name}</span>
                </div>
              </div>
              <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => handleDelete(p.id, p.title)}
                  disabled={deleting === p.id}
                  className="p-1.5 text-gray-400 hover:text-red-500 rounded-md hover:bg-red-50 transition-colors"
                  title="Удалить"
                >
                  {deleting === p.id ? <Spinner size={16} /> : <Trash2 className="w-4 h-4" />}
                </button>
                <Link
                  to={`/protocols/${p.id}`}
                  className="p-1.5 text-gray-400 hover:text-brand-600 rounded-md hover:bg-brand-50 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="flex items-center justify-center w-16 h-16 bg-brand-50 rounded-2xl mb-4">
        <FlaskConical className="w-8 h-8 text-brand-600" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-1">Протоколов пока нет</h3>
      <p className="text-gray-500 text-sm mb-6 max-w-sm">
        Создайте первый клинический протокол — AI сгенерирует все разделы в соответствии с ICH E6 GCP.
      </p>
      <Link to="/protocols/new" className="btn-primary">
        <Plus className="w-4 h-4" />
        Создать первый протокол
      </Link>
    </div>
  )
}
