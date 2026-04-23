import { useEffect, useState, useRef } from 'react'
import { api, type AuditEntry } from '../api/client'
import { Shield, Download, RefreshCcw, Filter, Clock, User, Activity } from 'lucide-react'
import Spinner from '../components/Spinner'
import ErrorAlert from '../components/ErrorAlert'

const ACTION_LABELS: Record<string, string> = {
  create:            'Создание',
  update:            'Обновление',
  delete:            'Удаление',
  ai_generate:       'AI Генерация',
  section_regenerate:'Перегенерация секции',
  consistency_check: 'GCP-проверка',
  export:            'Экспорт',
}

const ACTION_COLORS: Record<string, string> = {
  create:            'bg-emerald-50 text-emerald-700 border-emerald-200',
  update:            'bg-sky-50 text-sky-700 border-sky-200',
  delete:            'bg-red-50 text-red-700 border-red-200',
  ai_generate:       'bg-violet-50 text-violet-700 border-violet-200',
  section_regenerate:'bg-indigo-50 text-indigo-700 border-indigo-200',
  consistency_check: 'bg-amber-50 text-amber-700 border-amber-200',
  export:            'bg-gray-50 text-gray-600 border-gray-200',
}

const ROLE_COLORS: Record<string, string> = {
  admin:    'bg-red-100 text-red-700',
  employee: 'bg-sky-100 text-sky-700',
  auditor:  'bg-gray-100 text-gray-600',
  system:   'bg-gray-100 text-gray-500',
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString('ru', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

function MetaChip({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex gap-1 text-xs text-gray-500">
      <span className="text-gray-400">{label}:</span>
      <span className="text-gray-700 font-medium">{value}</span>
    </span>
  )
}

function AuditRow({ log, index }: { log: AuditEntry; index: number }) {
  const actionCls = ACTION_COLORS[log.action] ?? 'bg-gray-50 text-gray-600 border-gray-200'
  const role = (log.metadata?.role as string) || log.performed_by
  const roleCls = ROLE_COLORS[role] ?? ROLE_COLORS.system

  return (
    <tr className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
      {/* Timestamp */}
      <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap font-mono">
        {fmtDate(log.created_at)}
      </td>
      {/* Who */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-1.5">
          <User className="w-3 h-3 text-gray-400 flex-shrink-0" />
          <span className="text-sm text-gray-800 font-medium">{log.performed_by}</span>
          {log.metadata?.role != null && (
            <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${roleCls}`}>
              {String(log.metadata.role)}
            </span>
          )}
        </div>
      </td>
      {/* Action */}
      <td className="px-4 py-3">
        <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md border font-medium ${actionCls}`}>
          <Activity className="w-3 h-3" />
          {ACTION_LABELS[log.action] ?? log.action}
        </span>
      </td>
      {/* Entity */}
      <td className="px-4 py-3 text-xs text-gray-500 font-mono">
        {log.entity_type}/{log.entity_id.slice(0, 8)}…
      </td>
      {/* Details */}
      <td className="px-4 py-3">
        <div className="flex flex-wrap gap-x-3 gap-y-1">
          {log.metadata?.title != null && <MetaChip label="Протокол" value={String(log.metadata.title)} />}
          {log.metadata?.version != null && <MetaChip label="Версия" value={String(log.metadata.version)} />}
          {log.metadata?.model != null && <MetaChip label="Модель" value={String(log.metadata.model)} />}
          {log.metadata?.duration_ms != null && <MetaChip label="Время" value={`${String(log.metadata.duration_ms)}мс`} />}
          {log.metadata?.compliance_score != null && <MetaChip label="GCP Score" value={`${String(log.metadata.compliance_score)}%`} />}
          {Array.isArray(log.metadata?.fields) && <MetaChip label="Поля" value={(log.metadata.fields as string[]).join(', ')} />}
          {log.metadata?.section != null && <MetaChip label="Секция" value={String(log.metadata.section)} />}
          {log.metadata?.format != null && <MetaChip label="Формат" value={String(log.metadata.format)} />}
        </div>
      </td>
    </tr>
  )
}

export default function AuditTrailPage() {
  const today = new Date().toISOString().slice(0, 10)
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString().slice(0, 10)

  const [logs, setLogs] = useState<AuditEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [fromDate, setFromDate] = useState(thirtyDaysAgo)
  const [toDate, setToDate] = useState(today)
  const [actionFilter, setActionFilter] = useState('')
  const [userFilter, setUserFilter] = useState('')
  const printRef = useRef<HTMLDivElement>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.listAuditLog({
        from_date: fromDate || undefined,
        to_date:   toDate   || undefined,
        action:    actionFilter || undefined,
        performed_by: userFilter || undefined,
        limit: 500,
      })
      setLogs(data)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handlePrint = () => {
    window.print()
  }

  const printDate = new Date().toLocaleString('ru', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    timeZoneName: 'short',
  })

  return (
    <>
      {/* Print CSS */}
      <style>{`
        @media print {
          body * { visibility: hidden !important; }
          #audit-printable, #audit-printable * { visibility: visible !important; }
          #audit-printable { position: absolute; left: 0; top: 0; width: 100%; }
          #audit-no-print { display: none !important; }
          .print-header { display: block !important; }
          @page { margin: 15mm; size: A4 landscape; }
        }
        .print-header { display: none; }
      `}</style>

      <div>
        {/* Page header */}
        <div className="flex items-start justify-between mb-6 gap-4 flex-wrap" id="audit-no-print">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Shield className="w-6 h-6 text-brand-600" />
              Аудиторский след
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Все действия пользователей — кто, где, когда, зачем
            </p>
          </div>
          <button onClick={handlePrint} className="btn-secondary flex items-center gap-2">
            <Download className="w-4 h-4" />
            Печать / PDF
          </button>
        </div>

        {/* Filters */}
        <div className="card p-4 mb-4" id="audit-no-print">
          <div className="flex items-center gap-2 mb-3">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">Фильтры</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <label className="form-label text-xs mb-1">Дата от</label>
              <input
                type="date"
                className="form-input text-sm"
                value={fromDate}
                onChange={e => setFromDate(e.target.value)}
                max={toDate}
              />
            </div>
            <div>
              <label className="form-label text-xs mb-1">Дата до</label>
              <input
                type="date"
                className="form-input text-sm"
                value={toDate}
                onChange={e => setToDate(e.target.value)}
                min={fromDate}
              />
            </div>
            <div>
              <label className="form-label text-xs mb-1">Действие</label>
              <select
                className="form-input text-sm"
                value={actionFilter}
                onChange={e => setActionFilter(e.target.value)}
              >
                <option value="">Все действия</option>
                {Object.entries(ACTION_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="form-label text-xs mb-1">Пользователь</label>
              <input
                type="text"
                className="form-input text-sm"
                placeholder="admin, employee…"
                value={userFilter}
                onChange={e => setUserFilter(e.target.value)}
              />
            </div>
          </div>
          <div className="flex items-center gap-2 mt-3">
            <button onClick={load} className="btn-primary !py-1.5 text-sm flex items-center gap-1.5">
              <RefreshCcw className="w-3.5 h-3.5" />
              Применить
            </button>
            <span className="text-xs text-gray-400">
              {loading ? 'Загрузка…' : `Найдено: ${logs.length} событий`}
            </span>
          </div>
        </div>

        {error && <div className="mb-4"><ErrorAlert message={error} onClose={() => setError(null)} /></div>}

        {/* Printable area */}
        <div id="audit-printable" ref={printRef}>
          {/* Print header (hidden on screen) */}
          <div className="print-header mb-4">
            <div className="flex items-start justify-between mb-2">
              <div>
                <h1 className="text-lg font-bold">AI Protocol Generator — Аудиторский след</h1>
                <p className="text-sm text-gray-600">
                  FOR RESEARCH USE ONLY — NOT FOR CLINICAL USE
                </p>
              </div>
              <div className="text-right text-xs text-gray-500">
                <p className="font-medium">Дата печати: {printDate}</p>
                <p>Период: {fromDate || '—'} — {toDate || '—'}</p>
                {actionFilter && <p>Действие: {ACTION_LABELS[actionFilter] ?? actionFilter}</p>}
                {userFilter && <p>Пользователь: {userFilter}</p>}
                <p>Всего записей: {logs.length}</p>
              </div>
            </div>
            <hr className="border-gray-300 mb-3" />
            <p className="text-xs text-gray-500 italic">
              Документ сформирован автоматически. Является записью аудиторского следа системы.
              Все данные — синтетические, только для демонстрации.
            </p>
          </div>

          {/* Table */}
          {loading ? (
            <div className="flex justify-center py-16"><Spinner size={28} /></div>
          ) : logs.length === 0 ? (
            <div className="card p-12 text-center text-gray-400">
              <Clock className="w-8 h-8 mx-auto mb-2" />
              <p>Событий за выбранный период не найдено</p>
            </div>
          ) : (
            <div className="card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50">
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">Дата / Время</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Пользователь</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Действие</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Объект</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Детали</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {logs.map((log, i) => (
                      <AuditRow key={log.id} log={log} index={i} />
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Print footer */}
              <div className="print-header px-4 py-3 border-t border-gray-200 text-xs text-gray-400 text-right">
                AI Protocol Generator v0.5.0 · Всего записей: {logs.length} · Напечатано: {printDate}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
