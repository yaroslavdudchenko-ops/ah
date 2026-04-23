import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ChevronLeft, Zap, Download, Shield, Trash2, CheckCircle2,
  AlertTriangle, Info, FileText, RefreshCcw, RotateCcw
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { api, type Protocol, type ProtocolVersion, type GenerateStatus, type CheckResponse } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import StatusBadge from '../components/StatusBadge'
import Spinner from '../components/Spinner'
import ErrorAlert from '../components/ErrorAlert'

const SECTION_LABELS: Record<string, string> = {
  title_page:  'Титульная страница',
  synopsis:    'Краткое резюме',
  background:  'Введение / Обоснование',
  introduction:'Введение / Обоснование',
  objectives:  'Цели исследования',
  design:      'Дизайн исследования',
  population:  'Популяция',
  treatment:   'Лечение / Вмешательства',
  efficacy:    'Оценка эффективности',
  safety:      'Безопасность',
  statistics:  'Статистический анализ',
  ethics:      'Этические аспекты',
  references:  'Список литературы',
}

const POLL_INTERVAL = 2500

export default function ProtocolPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { isReadOnly } = useAuth()

  const [protocol, setProtocol]           = useState<Protocol | null>(null)
  const [versions, setVersions]           = useState<ProtocolVersion[]>([])
  const [activeVersion, setActiveVersion] = useState<ProtocolVersion | null>(null)
  const [generateStatus, setGenerateStatus] = useState<GenerateStatus | null>(null)
  const [checkResult, setCheckResult]     = useState<CheckResponse | null>(null)
  const [taskId, setTaskId]               = useState<string | null>(null)
  const [regenSection, setRegenSection]   = useState<string | null>(null)
  const [comment, setComment]             = useState('')

  const [loading, setLoading]     = useState(true)
  const [generating, setGenerating] = useState(false)
  const [checking, setChecking]   = useState(false)
  const [exporting, setExporting] = useState<string | null>(null)
  const [deleting, setDeleting]   = useState(false)
  const [error, setError]         = useState<string | null>(null)
  const [activeSection, setActiveSection] = useState<string | null>(null)

  const loadProtocol = useCallback(async () => {
    if (!id) return
    try {
      const [proto, vers] = await Promise.all([
        api.getProtocol(id),
        api.listVersions(id).catch(() => [] as ProtocolVersion[]),
      ])
      setProtocol(proto)
      setVersions(vers)
      if (vers.length > 0) {
        const latest = vers[vers.length - 1]
        setActiveVersion(latest)
        const keys = Object.keys(latest.content)
        if (keys.length > 0) setActiveSection(keys[0])
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { loadProtocol() }, [loadProtocol])

  // Poll generation / regen status
  useEffect(() => {
    if (!taskId || !id) return
    const timer = setInterval(async () => {
      try {
        const status = await api.getGenerateStatus(id, taskId)
        setGenerateStatus(status)
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(timer)
          setGenerating(false)
          setRegenSection(null)
          setTaskId(null)
          if (status.status === 'completed') {
            await loadProtocol()
          } else {
            setError(status.message || 'Ошибка генерации')
          }
        }
      } catch {
        clearInterval(timer)
        setGenerating(false)
        setRegenSection(null)
        setTaskId(null)
      }
    }, POLL_INTERVAL)
    return () => clearInterval(timer)
  }, [taskId, id, loadProtocol])

  const handleGenerate = async () => {
    if (!id) return
    setGenerating(true)
    setError(null)
    setCheckResult(null)
    try {
      const res = await api.startGenerate(id, comment || undefined)
      setComment('')
      setTaskId(res.task_id)
      setGenerateStatus({ task_id: res.task_id, status: 'pending', sections_done: 0, total_sections: 9 })
    } catch (e) {
      setError((e as Error).message)
      setGenerating(false)
    }
  }

  const handleRegenSection = async (sectionKey: string) => {
    if (!id) return
    setGenerating(true)
    setRegenSection(sectionKey)
    setError(null)
    try {
      const res = await api.regenerateSection(id, sectionKey)
      setTaskId(res.task_id)
      setGenerateStatus({ task_id: res.task_id, status: 'pending', sections_done: 0, total_sections: 1 })
    } catch (e) {
      setError((e as Error).message)
      setGenerating(false)
      setRegenSection(null)
    }
  }

  const handleCheck = async () => {
    if (!id) return
    setChecking(true)
    setError(null)
    try {
      const res = await api.checkConsistency(id)
      setCheckResult(res)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setChecking(false)
    }
  }

  const handleExport = async (format: 'md' | 'html' | 'docx') => {
    if (!id) return
    setExporting(format)
    try {
      await api.exportProtocol(id, format)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setExporting(null)
    }
  }

  const handleDelete = async () => {
    if (!id || !protocol) return
    if (!confirm(`Удалить протокол «${protocol.title}»? Это действие нельзя отменить.`)) return
    setDeleting(true)
    try {
      await api.deleteProtocol(id)
      navigate('/protocols')
    } catch (e) {
      setError((e as Error).message)
      setDeleting(false)
    }
  }

  if (loading) return <div className="flex justify-center py-24"><Spinner size={36} /></div>
  if (!protocol) return <div className="py-16"><ErrorAlert message="Протокол не найден" /></div>

  const sections = activeVersion ? Object.keys(activeVersion.content) : []
  const hasContent = sections.length > 0

  return (
    <div className="space-y-6">
      {/* Top bar */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <button onClick={() => navigate('/protocols')}
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-2">
            <ChevronLeft className="w-4 h-4" /> Назад
          </button>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl font-bold text-gray-900">{protocol.title}</h1>
            <StatusBadge status={protocol.status} />
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {protocol.drug_name} · {protocol.inn} · {protocol.therapeutic_area}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {!isReadOnly && (
            <button onClick={handleGenerate} disabled={generating || checking} className="btn-primary">
              {generating && !regenSection
                ? <><Spinner size={16} /> Генерация...</>
                : <><Zap className="w-4 h-4" /> Генерировать</>}
            </button>
          )}

          {hasContent && (
            <>
              {!isReadOnly && (
                <button onClick={handleCheck} disabled={checking || generating} className="btn-secondary">
                  {checking ? <><Spinner size={16} /> Проверка...</> : <><Shield className="w-4 h-4" /> GCP-проверка</>}
                </button>
              )}
              <div className="flex gap-1">
                {(['md', 'html', 'docx'] as const).map(fmt => (
                  <button key={fmt} onClick={() => handleExport(fmt)} disabled={!!exporting}
                    className="btn-secondary !px-3 text-xs uppercase">
                    {exporting === fmt ? <Spinner size={14} /> : <><Download className="w-3.5 h-3.5" />{fmt}</>}
                  </button>
                ))}
              </div>
            </>
          )}

          {!isReadOnly && (
            <button onClick={handleDelete} disabled={deleting} className="btn-danger !px-3">
              {deleting ? <Spinner size={16} /> : <Trash2 className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      {/* Version comment input */}
      {!isReadOnly && (
        <div className="card p-4">
          <label className="form-label mb-1">Комментарий к версии (опционально)</label>
          <input
            className="form-input"
            placeholder="Описание изменений, например: «Обновлены критерии включения»"
            value={comment}
            onChange={e => setComment(e.target.value)}
            maxLength={1000}
          />
        </div>
      )}

      {/* Generation progress */}
      {generating && generateStatus && (
        <div className="card p-4">
          <div className="flex items-center gap-3 mb-2">
            <Spinner size={18} />
            <span className="text-sm font-medium text-gray-700">
              {regenSection
                ? `Перегенерация раздела: ${SECTION_LABELS[regenSection] ?? regenSection}...`
                : `Генерация разделов... ${generateStatus.sections_done}/${generateStatus.total_sections}`}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-brand-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${(generateStatus.sections_done / Math.max(generateStatus.total_sections, 1)) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* GCP Check Result */}
      {checkResult && <GcpCheckPanel result={checkResult} onClose={() => setCheckResult(null)} />}

      {/* Meta card */}
      <div className="card p-5">
        <h2 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Info className="w-4 h-4 text-gray-400" /> Параметры протокола
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-3 text-sm">
          <MetaItem label="Фаза" value={protocol.phase} />
          <MetaItem label="Популяция" value={protocol.population} />
          <MetaItem label="Дозирование" value={protocol.dosing} />
          <MetaItem label="Длительность" value={`${protocol.duration_weeks} нед.`} />
          <MetaItem label="Первичная КТ" value={protocol.primary_endpoint} />
          {protocol.secondary_endpoints?.length > 0 && (
            <MetaItem label="Вторичные КТ" value={protocol.secondary_endpoints.join('; ')} />
          )}
        </div>
        {protocol.inclusion_criteria?.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-500 font-medium mb-1">Критерии включения</p>
            <ul className="text-sm text-gray-700 space-y-0.5">
              {protocol.inclusion_criteria.map((c, i) => <li key={i}>{i + 1}. {c}</li>)}
            </ul>
          </div>
        )}
      </div>

      {/* Content: sidebar + sections */}
      {hasContent && activeVersion ? (
        <div className="flex gap-6 items-start">
          {/* Sidebar */}
          <aside className="w-52 flex-shrink-0 card sticky top-20">
            <div className="p-3">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2 px-1">Разделы</p>
              <nav className="space-y-0.5">
                {sections.map(sec => (
                  <button
                    key={sec}
                    onClick={() => setActiveSection(sec)}
                    className={`w-full text-left px-2 py-1.5 rounded-md text-sm transition-colors ${
                      activeSection === sec
                        ? 'bg-brand-50 text-brand-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {SECTION_LABELS[sec] ?? sec}
                  </button>
                ))}
              </nav>

              {versions.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <p className="text-xs font-medium text-gray-500 mb-1 px-1">Версия</p>
                  <select
                    className="form-input text-xs"
                    value={activeVersion?.id}
                    onChange={e => {
                      const v = versions.find(v => v.id === e.target.value)
                      if (v) { setActiveVersion(v); setActiveSection(Object.keys(v.content)[0] ?? null) }
                    }}
                  >
                    {versions.map(v => (
                      <option key={v.id} value={v.id}>
                        v{v.version_number}{v.comment ? ` · ${v.comment.slice(0, 20)}` : ''}
                      </option>
                    ))}
                  </select>
                  {activeVersion.comment && (
                    <p className="text-xs text-gray-400 mt-1 px-1 italic">{activeVersion.comment}</p>
                  )}
                  {activeVersion.compliance_score !== undefined && (
                    <div className="mt-2 px-1">
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>GCP score</span>
                        <span className="font-medium">{Math.round(activeVersion.compliance_score * 100)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div
                          className="bg-emerald-500 h-1.5 rounded-full"
                          style={{ width: `${activeVersion.compliance_score * 100}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </aside>

          {/* Section content */}
          <div className="flex-1 min-w-0 card p-6">
            {activeSection && activeVersion.content[activeSection] ? (
              <>
                <div className="flex items-center justify-between gap-2 mb-4">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-brand-600" />
                    <h2 className="font-semibold text-gray-900">
                      {SECTION_LABELS[activeSection] ?? activeSection}
                    </h2>
                  </div>
                  {!isReadOnly && (
                    <button
                      onClick={() => handleRegenSection(activeSection)}
                      disabled={generating || checking}
                      title="Перегенерировать этот раздел"
                      className="btn-secondary !px-2 !py-1 text-xs flex items-center gap-1"
                    >
                      {regenSection === activeSection
                        ? <Spinner size={12} />
                        : <RotateCcw className="w-3.5 h-3.5" />}
                      Перегенерировать
                    </button>
                  )}
                </div>
                <div className="prose prose-sm max-w-none text-gray-700">
                  <ReactMarkdown>{activeVersion.content[activeSection]}</ReactMarkdown>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center py-12 text-gray-400">
                <FileText className="w-8 h-8 mb-2" />
                <p className="text-sm">Выберите раздел</p>
              </div>
            )}
          </div>
        </div>
      ) : !generating ? (
        <div className="card p-10 flex flex-col items-center text-center">
          <div className="w-16 h-16 bg-brand-50 rounded-2xl flex items-center justify-center mb-4">
            <Zap className="w-8 h-8 text-brand-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-1">Контент ещё не сгенерирован</h3>
          <p className="text-sm text-gray-500 mb-5 max-w-sm">
            Нажмите «Генерировать», и AI создаст все разделы протокола в соответствии с ICH E6(R2) GCP
          </p>
          {!isReadOnly && (
            <button onClick={handleGenerate} className="btn-primary">
              <Zap className="w-4 h-4" /> Генерировать протокол
            </button>
          )}
        </div>
      ) : null}
    </div>
  )
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-gray-900 font-medium truncate" title={value}>{value}</p>
    </div>
  )
}

function GcpCheckPanel({ result, onClose }: { result: CheckResponse; onClose: () => void }) {
  const score = Math.round(result.compliance_score * 100)
  const rfScore = Math.round((result.rf_compliance_score ?? 0) * 100)
  const scoreColor = score >= 80 ? 'text-emerald-600' : score >= 60 ? 'text-amber-600' : 'text-red-600'
  const barColor   = score >= 80 ? 'bg-emerald-500'  : score >= 60 ? 'bg-amber-500'   : 'bg-red-500'

  const sevColor: Record<string, string> = {
    high:   'text-red-700 bg-red-50 border-red-200',
    medium: 'text-amber-700 bg-amber-50 border-amber-200',
    low:    'text-blue-700 bg-blue-50 border-blue-200',
  }
  const SevIcon = ({ s }: { s: string }) =>
    s === 'high' ? <AlertTriangle className="w-4 h-4" /> : <Info className="w-4 h-4" />

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-900 flex items-center gap-2">
          <Shield className="w-4 h-4 text-brand-600" /> GCP/ICH Compliance Check
        </h2>
        <button onClick={onClose} className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1">
          <RefreshCcw className="w-3.5 h-3.5" /> Скрыть
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {[
          { label: 'ICH E6(R2) Score', score, color: scoreColor, bar: barColor },
          {
            label: 'РФ НМД Score', score: rfScore,
            color: rfScore >= 80 ? 'text-emerald-600' : rfScore >= 60 ? 'text-amber-600' : 'text-red-600',
            bar:   rfScore >= 80 ? 'bg-emerald-500'   : rfScore >= 60 ? 'bg-amber-500'   : 'bg-red-500',
          },
        ].map(({ label, score: s, color, bar }) => (
          <div key={label} className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">{label}</p>
            <p className={`text-2xl font-bold ${color}`}>{s}%</p>
            <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
              <div className={`${bar} h-1.5 rounded-full transition-all`} style={{ width: `${s}%` }} />
            </div>
          </div>
        ))}
      </div>

      <p className="text-sm text-gray-700">{result.summary}</p>

      {result.issues?.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Найдено замечаний: {result.issues.length}
          </p>
          {result.issues.map((issue, i) => (
            <div key={i} className={`flex gap-3 p-3 rounded-lg border ${sevColor[issue.severity] ?? sevColor.low}`}>
              <SevIcon s={issue.severity} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xs font-medium uppercase">{issue.severity}</span>
                  <span className="text-xs text-gray-500">· {SECTION_LABELS[issue.section] ?? issue.section}</span>
                </div>
                <p className="text-sm">{issue.description}</p>
                {issue.suggestion && (
                  <p className="text-xs mt-1 opacity-75 flex items-start gap-1">
                    <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0" />
                    {issue.suggestion}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-gray-400">
        AI-Assisted. Requires qualified person review. Не является юридической или медицинской экспертизой.
      </p>
    </div>
  )
}
