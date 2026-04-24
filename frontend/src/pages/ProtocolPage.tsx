import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ChevronLeft, Zap, Download, Shield, CheckCircle2,
  AlertTriangle, Info, FileText, RefreshCcw, RotateCcw, Clock, User, Activity, Tag, Lock, GitBranch,
  Send, ThumbsUp, MessageSquareWarning, ChevronDown, Copy, SlidersHorizontal, CheckCheck,
  GitCompare, BarChart3, FileSignature, X, Plus, Trash2
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { api, type Protocol, type ProtocolVersion, type GenerateStatus, type CheckResponse, type AuditEntry, type DiffSection } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import StatusBadge from '../components/StatusBadge'
import TagInput from '../components/TagInput'
import TagBadge from '../components/TagBadge'
import Spinner from '../components/Spinner'
import ErrorAlert from '../components/ErrorAlert'
import SynthiaOrb from '../components/SynthiaOrb'
import DraftModal from '../components/DraftModal'

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
  // Appendices (on-demand artifacts)
  sap:         'Appendix A: SAP',
  icf:         'Appendix B: ICF',
}

const POLL_INTERVAL = 2500

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

type PageTab = 'content' | 'audit'

export default function ProtocolPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { isReadOnly, user } = useAuth()

  const [tab, setTab] = useState<PageTab>('content')
  const [protocol, setProtocol]           = useState<Protocol | null>(null)
  const [allTags, setAllTags]             = useState<string[]>([])
  const [editingTags, setEditingTags]     = useState(false)
  const [draftTags, setDraftTags]         = useState<string[]>([])
  const [savingTags, setSavingTags]       = useState(false)
  const [versions, setVersions]           = useState<ProtocolVersion[]>([])
  const [activeVersion, setActiveVersion] = useState<ProtocolVersion | null>(null)
  const [generateStatus, setGenerateStatus] = useState<GenerateStatus | null>(null)
  const [checkResult, setCheckResult]     = useState<CheckResponse | null>(null)
  const [taskId, setTaskId]               = useState<string | null>(null)
  const [regenSection, setRegenSection]   = useState<string | null>(null)
  const [comment, setComment]             = useState('')
  const [auditLogs, setAuditLogs]         = useState<AuditEntry[]>([])
  const [auditLoading, setAuditLoading]   = useState(false)
  const [auditFrom, setAuditFrom]         = useState('')
  const [auditTo, setAuditTo]             = useState('')
  const [showDraft, setShowDraft]         = useState(false)

  const [loading, setLoading]     = useState(true)
  const [generating, setGenerating] = useState(false)
  const [checking, setChecking]   = useState(false)
  const [exporting, setExporting] = useState<string | null>(null)
  const [forking, setForking]             = useState(false)
  const [copying, setCopying]             = useState(false)
  const [statusUpdating, setStatusUpdating] = useState(false)
  const [customPrompt, setCustomPrompt]   = useState('')
  const [showPromptEditor, setShowPromptEditor] = useState(false)
  const [exportingIssues, setExportingIssues] = useState<string | null>(null)
  const [issuesDropdownOpen, setIssuesDropdownOpen] = useState(false)
  const issuesDropdownRef = useRef<HTMLDivElement>(null)
  const [error, setError]         = useState<string | null>(null)
  const [activeSection, setActiveSection] = useState<string | null>(null)

  // Edit meta state
  const [editingMeta, setEditingMeta]       = useState(false)
  const [metaForm, setMetaForm]             = useState<{
    title: string; drug_name: string; inn: string; phase: string
    therapeutic_area: string; indication: string; population: string
    primary_endpoint: string; secondary_endpoints: string[]
    duration_weeks: string; dosing: string
    inclusion_criteria: string[]; exclusion_criteria: string[]
  } | null>(null)
  const [savingMeta, setSavingMeta]         = useState(false)

  // Diff state
  const [showDiffPanel, setShowDiffPanel]   = useState(false)
  const [diffV1, setDiffV1]               = useState<number | null>(null)
  const [diffV2, setDiffV2]               = useState<number | null>(null)
  const [diffResult, setDiffResult]       = useState<DiffSection[] | null>(null)
  const [diffLoading, setDiffLoading]     = useState(false)
  const [diffError, setDiffError]         = useState<string | null>(null)

  // SAP/ICF generation state
  const [generatingArtifact, setGeneratingArtifact] = useState<'sap' | 'icf' | null>(null)

  // Protocol is locked once it has AI-generated versions
  const isLocked = versions.length > 0
  const isApproved = protocol?.status === 'approved'
  const isEmployee = user?.role === 'employee'
  // Creator cannot approve own protocol (4-eyes GCP principle)
  const isCreator = protocol?.created_by === user?.username

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

  useEffect(() => {
    if (!issuesDropdownOpen) return
    const handler = (e: MouseEvent) => {
      if (issuesDropdownRef.current && !issuesDropdownRef.current.contains(e.target as Node)) {
        setIssuesDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [issuesDropdownOpen])

  useEffect(() => { api.getAllTags().then(setAllTags).catch(() => {}) }, [])

  const handleSaveTags = async () => {
    if (!id) return
    setSavingTags(true)
    try {
      await api.updateProtocol(id, { tags: draftTags })
      setProtocol(p => p ? { ...p, tags: draftTags } : p)
      setEditingTags(false)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSavingTags(false)
    }
  }

  const loadAudit = useCallback(async () => {
    if (!id) return
    setAuditLoading(true)
    try {
      const data = await api.listProtocolAudit(id, {
        from_date: auditFrom || undefined,
        to_date:   auditTo   || undefined,
      })
      setAuditLogs(data)
    } catch {
      /* ignore */
    } finally {
      setAuditLoading(false)
    }
  }, [id, auditFrom, auditTo])

  useEffect(() => { if (tab === 'audit') loadAudit() }, [tab, loadAudit])

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
      const res = await api.startGenerate(id, comment || undefined, customPrompt || undefined)
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

  const handleStatusUpdate = async (newStatus: string) => {
    if (!id || !protocol) return
    setStatusUpdating(true)
    setError(null)
    try {
      const updated = await api.updateStatus(id, newStatus)
      setProtocol(updated)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setStatusUpdating(false)
    }
  }

  const startEditMeta = () => {
    if (!protocol) return
    setMetaForm({
      title: protocol.title,
      drug_name: protocol.drug_name,
      inn: protocol.inn,
      phase: protocol.phase,
      therapeutic_area: protocol.therapeutic_area,
      indication: protocol.indication,
      population: protocol.population,
      primary_endpoint: protocol.primary_endpoint,
      secondary_endpoints: protocol.secondary_endpoints?.length ? protocol.secondary_endpoints : [''],
      duration_weeks: String(protocol.duration_weeks),
      dosing: protocol.dosing,
      inclusion_criteria: protocol.inclusion_criteria?.length ? protocol.inclusion_criteria : [''],
      exclusion_criteria: protocol.exclusion_criteria?.length ? protocol.exclusion_criteria : [''],
    })
    setEditingMeta(true)
  }

  const handleSaveMeta = async () => {
    if (!id || !metaForm) return
    setSavingMeta(true)
    setError(null)
    try {
      const updated = await api.updateProtocol(id, {
        ...metaForm,
        duration_weeks: Number(metaForm.duration_weeks),
        secondary_endpoints: metaForm.secondary_endpoints.filter(s => s.trim()),
        inclusion_criteria: metaForm.inclusion_criteria.filter(s => s.trim()),
        exclusion_criteria: metaForm.exclusion_criteria.filter(s => s.trim()),
      })
      setProtocol(updated)
      setEditingMeta(false)
      setMetaForm(null)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSavingMeta(false)
    }
  }

  const handleExportIssues = async (format: 'json' | 'csv') => {
    if (!id) return
    setExportingIssues(format)
    try {
      await api.exportOpenIssues(id, format)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setExportingIssues(null)
    }
  }

  const handleCopy = async () => {
    if (!id || !protocol) return
    if (!confirm(`Создать копию протокола «${protocol.title}» в статусе "Черновик"?\n\nИсходный протокол останется без изменений.`)) return
    setCopying(true)
    setError(null)
    try {
      const copy = await api.copyProtocol(id)
      navigate(`/protocols/${copy.id}`)
    } catch (e) {
      setError((e as Error).message)
      setCopying(false)
    }
  }

  const handleFork = async () => {
    if (!id || !protocol) return
    if (!confirm(`Создать новую редактируемую ревизию протокола «${protocol.title}»?\n\nТекущий протокол будет архивирован.`)) return
    setForking(true)
    setError(null)
    try {
      const fork = await api.forkProtocol(id)
      navigate(`/protocols/${fork.id}`)
    } catch (e) {
      setError((e as Error).message)
      setForking(false)
    }
  }

  const handleLoadDiff = async () => {
    if (!id || versions.length < 2) return
    const v1 = diffV1 ?? versions[0].version_number
    const v2 = diffV2 ?? versions[versions.length - 1].version_number
    setDiffLoading(true)
    setDiffError(null)
    try {
      const res = await api.getDiff(id, v1, v2)
      setDiffResult(res.sections)
    } catch (e) {
      setDiffError((e as Error).message)
    } finally {
      setDiffLoading(false)
    }
  }

  const handleGenerateArtifact = async (artifact: 'sap' | 'icf') => {
    if (!id) return
    setGeneratingArtifact(artifact)
    setError(null)
    try {
      const { task_id } = await api.regenerateSection(id, artifact)
      // Poll until done
      let attempts = 0
      while (attempts < 60) {
        await new Promise(r => setTimeout(r, 2500))
        const st = await api.getGenerateStatus(id, task_id)
        if (st.status === 'completed' || st.status === 'failed') break
        attempts++
      }
      await loadProtocol()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setGeneratingArtifact(null)
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
            {isLocked && (
              <span
                title="Протокол заблокирован для редактирования. Параметры дизайна исследования неизменны после AI-генерации (GCP/ALCOA++)."
                className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md border bg-amber-50 text-amber-700 border-amber-200 cursor-default"
              >
                <Lock className="w-3 h-3" /> Заблокирован
              </span>
            )}
            {isApproved && (
              <span
                title="Протокол одобрен. Генерация и редактирование отключены."
                className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md border bg-emerald-50 text-emerald-700 border-emerald-200 cursor-default"
              >
                <CheckCheck className="w-3 h-3" /> Одобрен
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-1 flex flex-wrap items-center gap-x-1 min-w-0">
            <span className="truncate max-w-[220px]" title={protocol.drug_name}>{protocol.drug_name}</span>
            <span>·</span>
            <span className="truncate max-w-[220px]" title={protocol.inn}>{protocol.inn}</span>
            <span>·</span>
            <span>{protocol.therapeutic_area}</span>
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Generate — hidden for approved protocols */}
          {!isReadOnly && !isLocked && !isApproved && (
            <button onClick={handleGenerate} disabled={generating || checking} className="btn-primary">
              {generating && !regenSection
                ? <><Spinner size={16} /> Генерация...</>
                : <><Zap className="w-4 h-4" /> Генерировать</>}
            </button>
          )}
          {/* Re-generate button (has content, not approved) */}
          {!isReadOnly && isLocked && !isApproved && (
            <button onClick={handleGenerate} disabled={generating || checking} className="btn-secondary flex items-center gap-1.5 !text-violet-700 !border-violet-300 hover:!bg-violet-50">
              {generating && !regenSection
                ? <><Spinner size={16} /> Генерация...</>
                : <><RotateCcw className="w-4 h-4" /> Перегенерировать</>}
            </button>
          )}
          {/* Fork — create revision (archives source) */}
          {isLocked && isEmployee && !isApproved && (
            <button onClick={handleFork} disabled={forking} className="btn-secondary flex items-center gap-1.5">
              {forking ? <Spinner size={16} /> : <GitBranch className="w-4 h-4" />}
              Ревизия
            </button>
          )}
          {/* Copy — creates independent draft without archiving source */}
          {!isReadOnly && (
            <button onClick={handleCopy} disabled={copying} className="btn-secondary flex items-center gap-1.5">
              {copying ? <Spinner size={16} /> : <Copy className="w-4 h-4" />}
              Копия
            </button>
          )}

          {/* Status transition buttons */}
          {!isReadOnly && hasContent && (
            <>
              {protocol.status === 'draft' && (
                <button
                  onClick={() => handleStatusUpdate('in_review')}
                  disabled={statusUpdating}
                  title="Отправить протокол на рецензирование"
                  className="btn-secondary flex items-center gap-1.5 !text-sky-700 !border-sky-300 hover:!bg-sky-50"
                >
                  {statusUpdating ? <Spinner size={16} /> : <Send className="w-4 h-4" />}
                  На ревью
                </button>
              )}
              {/* Approve: only admin, only NOT the creator (4-eyes GCP principle) */}
              {protocol.status === 'in_review' && user?.role === 'admin' && !isCreator && (
                <button
                  onClick={() => handleStatusUpdate('approved')}
                  disabled={statusUpdating}
                  title="Одобрить протокол (4-eyes: только другой пользователь)"
                  className="btn-secondary flex items-center gap-1.5 !text-emerald-700 !border-emerald-300 hover:!bg-emerald-50"
                >
                  {statusUpdating ? <Spinner size={16} /> : <CheckCheck className="w-4 h-4" />}
                  Одобрить
                </button>
              )}
              {protocol.status === 'in_review' && user?.role === 'admin' && isCreator && (
                <span
                  title="Вы создали этот протокол. Одобрение должен выполнить другой администратор (принцип 4-eyes, GCP)."
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-400 cursor-not-allowed select-none"
                >
                  <CheckCheck className="w-4 h-4" /> Одобрить
                </span>
              )}
            </>
          )}

          {hasContent && (
            <>
              <button
                onClick={() => setShowDraft(true)}
                className="btn-secondary"
                title="Просмотр полного черновика документа"
              >
                <FileText className="w-4 h-4" /> Черновик
              </button>
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
              <div className="relative" ref={issuesDropdownRef}>
                <button
                  onClick={() => setIssuesDropdownOpen(o => !o)}
                  disabled={!!exportingIssues}
                  title="Экспорт открытых вопросов (FR-07.4)"
                  className="btn-secondary flex items-center gap-1.5 !text-amber-700 !border-amber-300 hover:!bg-amber-50"
                >
                  {exportingIssues
                    ? <Spinner size={14} />
                    : <MessageSquareWarning className="w-4 h-4" />}
                  Открытые вопросы
                  <ChevronDown className={`w-3.5 h-3.5 transition-transform ${issuesDropdownOpen ? 'rotate-180' : ''}`} />
                </button>
                {issuesDropdownOpen && (
                  <div className="absolute right-0 top-full mt-1 z-20 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[160px]">
                    {(['json', 'csv'] as const).map(fmt => (
                      <button
                        key={fmt}
                        onClick={() => { setIssuesDropdownOpen(false); handleExportIssues(fmt) }}
                        disabled={!!exportingIssues}
                        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-amber-50 hover:text-amber-700 transition-colors"
                      >
                        <Download className="w-3.5 h-3.5 text-amber-500" />
                        Скачать {fmt.toUpperCase()}
                      </button>
                    ))}
                    <div className="border-t border-gray-100 mx-2 mt-1 pt-1">
                      <p className="px-2 pb-1 text-[10px] text-gray-400 leading-tight">
                        Открытые замечания GCP-проверки
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      {/* Version comment + custom prompt */}
      {!isReadOnly && !isApproved && (
        <div className="card p-4 space-y-3">
          <div>
            <label className="form-label mb-1">Комментарий к версии (опционально)</label>
            <input
              className="form-input"
              placeholder="Описание изменений, например: «Уточнены критерии включения»"
              value={comment}
              onChange={e => setComment(e.target.value)}
              maxLength={1000}
            />
          </div>
          {/* Custom prompt expander */}
          <div>
            <button
              type="button"
              onClick={() => setShowPromptEditor(v => !v)}
              className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-brand-600 transition-colors font-medium"
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              {showPromptEditor ? 'Скрыть настройку промпта' : 'Настроить промпт для AI'}
              <ChevronDown className={`w-3 h-3 transition-transform ${showPromptEditor ? 'rotate-180' : ''}`} />
            </button>
            {showPromptEditor && (
              <div className="mt-2 space-y-1">
                <label className="form-label text-xs">
                  Дополнительные инструкции для AI-генерации
                </label>
                <textarea
                  className="form-input text-sm resize-none"
                  rows={3}
                  placeholder="Например: «Акцент на педиатрическую популяцию», «Используй более формальный стиль», «Добавь раздел о фармакогенетике»"
                  value={customPrompt}
                  onChange={e => setCustomPrompt(e.target.value)}
                  maxLength={2000}
                />
                <p className="text-xs text-gray-400">Эти инструкции будут добавлены к каждому промпту при генерации.</p>
              </div>
            )}
          </div>
          {isLocked && isEmployee && (
            <p className="text-xs text-amber-600 flex items-center gap-1">
              <Lock className="w-3 h-3" />
              Протокол заблокирован. Используйте «Ревизия» — текущая версия будет архивирована (GCP ALCOA++).
            </p>
          )}
        </div>
      )}

      {/* Generation progress — Synthia Orb */}
      {generating && generateStatus && (
        <div className="card flex justify-center">
          <SynthiaOrb
            sections_done={generateStatus.sections_done}
            total_sections={generateStatus.total_sections}
            regenSection={regenSection}
            sectionLabel={regenSection ? (SECTION_LABELS[regenSection] ?? regenSection) : undefined}
          />
        </div>
      )}

      {/* GCP Check Result */}
      {checkResult && <GcpCheckPanel result={checkResult} onClose={() => setCheckResult(null)} />}

      {/* Tab switcher */}
      <div className="flex gap-1 border-b border-gray-200">
        {([['content', 'Содержание', FileText], ['audit', 'Аудит', Clock]] as const).map(([key, label, Icon]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === key
                ? 'border-brand-600 text-brand-700'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            {label}
          </button>
        ))}
      </div>

      {/* ── Content tab ── */}
      {tab === 'content' && (<>

      {/* Tags card */}
      <div className="card p-4">
        <div className="flex items-center justify-between gap-2 mb-2">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2 text-sm">
            <Tag className="w-4 h-4 text-gray-400" /> Теги
          </h2>
          {!isReadOnly && !editingTags && (
            <button
              onClick={() => { setDraftTags(protocol?.tags ?? []); setEditingTags(true) }}
              className="text-xs text-brand-600 hover:text-brand-700 font-medium"
            >
              Изменить
            </button>
          )}
        </div>
        {editingTags ? (
          <div className="space-y-2">
            <TagInput
              value={draftTags}
              onChange={setDraftTags}
              suggestions={allTags}
              placeholder="Добавить тег…"
            />
            <div className="flex gap-2">
              <button onClick={handleSaveTags} disabled={savingTags} className="btn-primary !py-1.5 text-xs">
                {savingTags ? <Spinner size={12} /> : 'Сохранить'}
              </button>
              <button onClick={() => setEditingTags(false)} className="btn-secondary !py-1.5 text-xs">
                Отмена
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {(protocol?.tags ?? []).length === 0 ? (
              <span className="text-sm text-gray-400">Теги не добавлены</span>
            ) : (
              (protocol?.tags ?? []).map(tag => <TagBadge key={tag} tag={tag} />)
            )}
          </div>
        )}
      </div>

      {/* Meta card */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <Info className="w-4 h-4 text-gray-400" /> Параметры протокола
          </h2>
          {!isReadOnly && !isApproved && !editingMeta && (
            <button
              onClick={startEditMeta}
              className="text-xs text-brand-600 hover:text-brand-700 flex items-center gap-1 px-2 py-1 rounded border border-brand-200 hover:bg-brand-50 transition-colors"
            >
              <RefreshCcw className="w-3 h-3" /> Редактировать
            </button>
          )}
        </div>

        {editingMeta && metaForm ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="form-label">Название *</label>
                <input className="form-input text-sm" value={metaForm.title}
                  onChange={e => setMetaForm(f => f && ({ ...f, title: e.target.value }))} />
              </div>
              <div>
                <label className="form-label">Фаза *</label>
                <select className="form-input text-sm" value={metaForm.phase}
                  onChange={e => setMetaForm(f => f && ({ ...f, phase: e.target.value }))}>
                  {['I','II','III'].map(p => <option key={p} value={p}>Фаза {p}</option>)}
                </select>
              </div>
              <div>
                <label className="form-label">МНН (INN) *</label>
                <input className="form-input text-sm" value={metaForm.inn}
                  onChange={e => setMetaForm(f => f && ({ ...f, inn: e.target.value }))} />
              </div>
              <div>
                <label className="form-label">Торговое наименование / Код *</label>
                <input className="form-input text-sm" value={metaForm.drug_name}
                  onChange={e => setMetaForm(f => f && ({ ...f, drug_name: e.target.value }))} />
              </div>
            </div>
            <div>
              <label className="form-label">Показание / Нозология *</label>
              <textarea className="form-input text-sm" rows={2} value={metaForm.indication}
                onChange={e => setMetaForm(f => f && ({ ...f, indication: e.target.value }))} />
            </div>
            <div>
              <label className="form-label">Популяция пациентов *</label>
              <textarea className="form-input text-sm" rows={2} value={metaForm.population}
                onChange={e => setMetaForm(f => f && ({ ...f, population: e.target.value }))} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="form-label">Режим дозирования *</label>
                <input className="form-input text-sm" value={metaForm.dosing}
                  onChange={e => setMetaForm(f => f && ({ ...f, dosing: e.target.value }))} />
              </div>
              <div>
                <label className="form-label">Длительность (недели) *</label>
                <input type="number" className="form-input text-sm" value={metaForm.duration_weeks}
                  onChange={e => setMetaForm(f => f && ({ ...f, duration_weeks: e.target.value }))} />
              </div>
            </div>
            <div>
              <label className="form-label">Первичная конечная точка *</label>
              <textarea className="form-input text-sm" rows={2} value={metaForm.primary_endpoint}
                onChange={e => setMetaForm(f => f && ({ ...f, primary_endpoint: e.target.value }))} />
            </div>
            <div>
              <label className="form-label text-xs text-gray-500">Вторичные конечные точки</label>
              {metaForm.secondary_endpoints.map((ep, i) => (
                <div key={i} className="flex gap-2 mb-1">
                  <input className="form-input text-sm" value={ep}
                    onChange={e => setMetaForm(f => f && ({ ...f, secondary_endpoints: f.secondary_endpoints.map((v, j) => j === i ? e.target.value : v) }))} />
                  {metaForm.secondary_endpoints.length > 1 && (
                    <button type="button" onClick={() => setMetaForm(f => f && ({ ...f, secondary_endpoints: f.secondary_endpoints.filter((_, j) => j !== i) }))}
                      className="p-1.5 text-gray-400 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                  )}
                </div>
              ))}
              <button type="button" onClick={() => setMetaForm(f => f && ({ ...f, secondary_endpoints: [...f.secondary_endpoints, ''] }))}
                className="text-xs text-brand-600 hover:text-brand-700 flex items-center gap-1 mt-1">
                <Plus className="w-3 h-3" /> Добавить
              </button>
            </div>
            <div>
              <label className="form-label text-xs text-gray-500">Критерии включения</label>
              {metaForm.inclusion_criteria.map((c, i) => (
                <div key={i} className="flex gap-2 mb-1 items-center">
                  <span className="text-xs text-gray-400 w-5 text-right flex-shrink-0">{i+1}.</span>
                  <input className="form-input text-sm" value={c}
                    onChange={e => setMetaForm(f => f && ({ ...f, inclusion_criteria: f.inclusion_criteria.map((v, j) => j === i ? e.target.value : v) }))} />
                  {metaForm.inclusion_criteria.length > 1 && (
                    <button type="button" onClick={() => setMetaForm(f => f && ({ ...f, inclusion_criteria: f.inclusion_criteria.filter((_, j) => j !== i) }))}
                      className="p-1.5 text-gray-400 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                  )}
                </div>
              ))}
              <button type="button" onClick={() => setMetaForm(f => f && ({ ...f, inclusion_criteria: [...f.inclusion_criteria, ''] }))}
                className="text-xs text-brand-600 hover:text-brand-700 flex items-center gap-1 mt-1">
                <Plus className="w-3 h-3" /> Добавить
              </button>
            </div>
            <div>
              <label className="form-label text-xs text-gray-500">Критерии исключения</label>
              {metaForm.exclusion_criteria.map((c, i) => (
                <div key={i} className="flex gap-2 mb-1 items-center">
                  <span className="text-xs text-gray-400 w-5 text-right flex-shrink-0">{i+1}.</span>
                  <input className="form-input text-sm" value={c}
                    onChange={e => setMetaForm(f => f && ({ ...f, exclusion_criteria: f.exclusion_criteria.map((v, j) => j === i ? e.target.value : v) }))} />
                  {metaForm.exclusion_criteria.length > 1 && (
                    <button type="button" onClick={() => setMetaForm(f => f && ({ ...f, exclusion_criteria: f.exclusion_criteria.filter((_, j) => j !== i) }))}
                      className="p-1.5 text-gray-400 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                  )}
                </div>
              ))}
              <button type="button" onClick={() => setMetaForm(f => f && ({ ...f, exclusion_criteria: [...f.exclusion_criteria, ''] }))}
                className="text-xs text-brand-600 hover:text-brand-700 flex items-center gap-1 mt-1">
                <Plus className="w-3 h-3" /> Добавить
              </button>
            </div>
            <div className="flex gap-2 pt-2 border-t border-gray-100">
              <button onClick={handleSaveMeta} disabled={savingMeta} className="btn-primary !py-1.5 text-xs">
                {savingMeta ? <><Spinner size={14} /> Сохранение...</> : 'Сохранить'}
              </button>
              <button onClick={() => { setEditingMeta(false); setMetaForm(null) }} disabled={savingMeta} className="btn-secondary !py-1.5 text-xs">
                Отмена
              </button>
            </div>
          </div>
        ) : (
          <>
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
            {protocol.exclusion_criteria?.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <p className="text-xs text-gray-500 font-medium mb-1">Критерии исключения</p>
                <ul className="text-sm text-gray-700 space-y-0.5">
                  {protocol.exclusion_criteria.map((c, i) => <li key={i}>{i + 1}. {c}</li>)}
                </ul>
              </div>
            )}
          </>
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
                        v{v.version_number}{v.is_archived ? ' [Archive]' : ' [Active]'}{v.comment ? ` · ${v.comment.slice(0, 18)}` : ''}
                      </option>
                    ))}
                  </select>
                  {activeVersion.is_archived && (
                    <div className="flex items-center gap-1 mt-1.5 px-1">
                      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border bg-gray-50 text-gray-500 border-gray-200">
                        Archive — версия заменена новой
                      </span>
                    </div>
                  )}
                  {activeVersion.comment && (
                    <p className="text-xs text-gray-400 mt-1 px-1 italic">{activeVersion.comment}</p>
                  )}
                  {activeVersion.compliance_score !== undefined && (
                      <div className="mt-2 px-1">
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                          <span>GCP score</span>
                          <span className="font-medium">{Math.round(activeVersion.compliance_score)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div
                            className="bg-emerald-500 h-1.5 rounded-full"
                            style={{ width: `${Math.min(activeVersion.compliance_score, 100)}%` }}
                          />
                        </div>
                      </div>
                  )}
                  {/* Diff button — available when ≥2 versions exist */}
                  {versions.length >= 2 && (
                    <button
                      onClick={() => { setShowDiffPanel(true); handleLoadDiff() }}
                      className="mt-2 w-full btn btn-outline text-xs flex items-center justify-center gap-1"
                    >
                      <GitCompare className="w-3.5 h-3.5" /> Сравнить версии
                    </button>
                  )}
                </div>
              )}

              {/* SAP & ICF artifact generation (Appendix A & B) */}
              {hasContent && !isReadOnly && (
                <div className="mt-3 pt-3 border-t border-gray-100 space-y-1.5">
                  <p className="text-xs font-medium text-gray-500 px-1">Артефакты</p>
                  {(['sap', 'icf'] as const).map(artifact => {
                    const exists = activeVersion && artifact in activeVersion.content
                    const isGenerating = generatingArtifact === artifact
                    return (
                      <button
                        key={artifact}
                        onClick={() => {
                          if (!isApproved) handleGenerateArtifact(artifact)
                          else if (exists) setActiveSection(artifact)
                        }}
                        disabled={isApproved && !exists}
                        className={`w-full text-left text-xs px-2 py-1.5 rounded flex items-center gap-1.5 border transition-colors ${
                          exists
                            ? 'border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100'
                            : isApproved
                            ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                            : 'border-dashed border-gray-300 text-gray-500 hover:border-indigo-300 hover:text-indigo-600'
                        }`}
                      >
                        {artifact === 'sap'
                          ? <BarChart3 className="w-3.5 h-3.5 shrink-0" />
                          : <FileSignature className="w-3.5 h-3.5 shrink-0" />
                        }
                        <span className="truncate">
                          {isGenerating ? 'Генерация...' : exists
                            ? (artifact === 'sap' ? 'Appendix A: SAP' : 'Appendix B: ICF')
                            : (artifact === 'sap' ? 'Сгенерировать SAP' : 'Сгенерировать ICF')
                          }
                        </span>
                        {isGenerating && <Spinner size={12} />}
                        {exists && !isGenerating && !isApproved && (
                          <RotateCcw className="w-3 h-3 ml-auto shrink-0 opacity-50" />
                        )}
                      </button>
                    )
                  })}
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
                  {!isReadOnly && !isApproved && (
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
          {!isReadOnly && !isLocked && (
            <button onClick={handleGenerate} className="btn-primary">
              <Zap className="w-4 h-4" /> Генерировать протокол
            </button>
          )}
        </div>
      ) : null}

      </>)}

      {/* ── Audit tab ── */}
      {tab === 'audit' && (
        <ProtocolAuditPanel
          logs={auditLogs}
          loading={auditLoading}
          fromDate={auditFrom}
          toDate={auditTo}
          onFromDate={setAuditFrom}
          onToDate={setAuditTo}
          onRefresh={loadAudit}
          protocolTitle={protocol.title}
        />
      )}

      {/* Draft viewer modal */}
      {showDraft && activeVersion && (
        <DraftModal
          version={activeVersion}
          protocolTitle={protocol.title}
          onClose={() => setShowDraft(false)}
        />
      )}

      {/* ── Diff panel (slide-over modal) ─────────────────────────────── */}
      {showDiffPanel && (
        <div className="fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-black/40" onClick={() => setShowDiffPanel(false)} />
          <div className="relative ml-auto w-full max-w-3xl bg-white shadow-2xl flex flex-col h-full overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 shrink-0">
              <div className="flex items-center gap-2">
                <GitCompare className="w-5 h-5 text-indigo-600" />
                <h2 className="text-base font-semibold text-gray-800">Сравнение версий</h2>
              </div>
              <button onClick={() => setShowDiffPanel(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Version selectors */}
            <div className="flex items-center gap-3 px-6 py-3 border-b border-gray-100 bg-gray-50 shrink-0 flex-wrap">
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-500 font-medium">Версия A:</label>
                <select
                  className="form-input text-xs py-1"
                  value={diffV1 ?? versions[0]?.version_number ?? ''}
                  onChange={e => setDiffV1(Number(e.target.value))}
                >
                  {versions.map(v => (
                    <option key={v.id} value={v.version_number}>v{v.version_number}{v.is_archived ? ' [Archive]' : ''}</option>
                  ))}
                </select>
              </div>
              <span className="text-gray-300 font-bold">→</span>
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-500 font-medium">Версия B:</label>
                <select
                  className="form-input text-xs py-1"
                  value={diffV2 ?? versions[versions.length - 1]?.version_number ?? ''}
                  onChange={e => setDiffV2(Number(e.target.value))}
                >
                  {versions.map(v => (
                    <option key={v.id} value={v.version_number}>v{v.version_number}{v.is_archived ? ' [Archive]' : ''}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleLoadDiff}
                disabled={diffLoading}
                className="btn btn-primary text-xs px-3 py-1.5 ml-auto"
              >
                {diffLoading ? <Spinner size={14} /> : <><RefreshCcw className="w-3.5 h-3.5" /> Обновить</>}
              </button>
            </div>

            {/* Diff body */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {diffError && <ErrorAlert message={diffError} />}
              {diffLoading && <div className="flex justify-center py-12"><Spinner size={28} /></div>}
              {!diffLoading && diffResult && (
                diffResult.length === 0 ? (
                  <p className="text-center text-gray-400 py-8">Нет разделов для сравнения</p>
                ) : (
                  diffResult.map(sec => (
                    <div key={sec.section} className={`rounded-lg border ${sec.changed ? 'border-amber-200' : 'border-gray-100'}`}>
                      <div className={`flex items-center justify-between px-4 py-2 rounded-t-lg text-sm font-medium ${sec.changed ? 'bg-amber-50 text-amber-800' : 'bg-gray-50 text-gray-500'}`}>
                        <span>{SECTION_LABELS[sec.section] ?? sec.section}</span>
                        {sec.changed
                          ? <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200">изменён</span>
                          : <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-400">без изменений</span>
                        }
                      </div>
                      {sec.changed && (
                        <div className="p-0 overflow-x-auto">
                          <pre className="text-[11px] leading-5 font-mono p-4 whitespace-pre-wrap">
                            {sec.diff.split('\n').map((line: string, i: number) => (
                              <span
                                key={i}
                                className={`block ${
                                  line.startsWith('+') && !line.startsWith('+++')
                                    ? 'bg-emerald-50 text-emerald-800'
                                    : line.startsWith('-') && !line.startsWith('---')
                                    ? 'bg-red-50 text-red-700'
                                    : line.startsWith('@@')
                                    ? 'bg-sky-50 text-sky-600'
                                    : 'text-gray-600'
                                }`}
                              >
                                {line || '\u00A0'}
                              </span>
                            ))}
                          </pre>
                        </div>
                      )}
                    </div>
                  ))
                )
              )}
              {!diffLoading && !diffResult && !diffError && (
                <p className="text-center text-gray-400 py-8">Выберите версии и нажмите «Обновить»</p>
              )}
            </div>
          </div>
        </div>
      )}
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
  const score = Math.round(result.compliance_score)
  const rfScore = Math.round(result.rf_compliance_score ?? 0)
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

// ── Per-protocol Audit Panel ─────────────────────────────────────────────────

interface AuditPanelProps {
  logs: AuditEntry[]
  loading: boolean
  fromDate: string
  toDate: string
  onFromDate: (v: string) => void
  onToDate:   (v: string) => void
  onRefresh:  () => void
  protocolTitle: string
}

function ProtocolAuditPanel({
  logs, loading, fromDate, toDate, onFromDate, onToDate, onRefresh, protocolTitle,
}: AuditPanelProps) {
  const printDate = new Date().toLocaleString('ru', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit', timeZoneName: 'short',
  })

  return (
    <>
      <style>{`
        @media print {
          body * { visibility: hidden !important; }
          #proto-audit-print, #proto-audit-print * { visibility: visible !important; }
          #proto-audit-print { position: absolute; left: 0; top: 0; width: 100%; }
          .proto-audit-noprint { display: none !important; }
          .proto-audit-phdr { display: block !important; }
          @page { margin: 15mm; size: A4 landscape; }
        }
        .proto-audit-phdr { display: none; }
      `}</style>

      {/* Filter bar */}
      <div className="card p-4 proto-audit-noprint">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="form-label text-xs mb-1">Дата от</label>
            <input type="date" className="form-input text-sm" value={fromDate}
              onChange={e => onFromDate(e.target.value)} max={toDate} />
          </div>
          <div>
            <label className="form-label text-xs mb-1">Дата до</label>
            <input type="date" className="form-input text-sm" value={toDate}
              onChange={e => onToDate(e.target.value)} min={fromDate} />
          </div>
          <button onClick={onRefresh} className="btn-primary !py-2 text-sm flex items-center gap-1.5">
            <RefreshCcw className="w-3.5 h-3.5" />
            Применить
          </button>
          <button onClick={() => window.print()} className="btn-secondary !py-2 text-sm flex items-center gap-1.5 ml-auto">
            <Download className="w-3.5 h-3.5" />
            Печать / PDF
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          {loading ? 'Загрузка…' : `Событий: ${logs.length}`}
        </p>
      </div>

      {/* Printable area */}
      <div id="proto-audit-print">
        {/* Print header */}
        <div className="proto-audit-phdr mb-4">
          <div className="flex justify-between">
            <div>
              <h1 className="text-base font-bold">Аудиторский след протокола</h1>
              <p className="text-sm font-medium">{protocolTitle}</p>
              <p className="text-xs text-gray-500">FOR RESEARCH USE ONLY — NOT FOR CLINICAL USE</p>
            </div>
            <div className="text-right text-xs text-gray-500">
              <p className="font-medium">Дата печати: {printDate}</p>
              {fromDate && <p>Период от: {fromDate}</p>}
              {toDate && <p>Период до: {toDate}</p>}
              <p>Всего событий: {logs.length}</p>
            </div>
          </div>
          <hr className="border-gray-300 my-2" />
          <p className="text-xs text-gray-400 italic">
            Документ сформирован автоматически. Является записью аудиторского следа системы.
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-16"><Spinner size={28} /></div>
        ) : logs.length === 0 ? (
          <div className="card p-12 text-center text-gray-400">
            <Clock className="w-8 h-8 mx-auto mb-2" />
            <p className="text-sm">Событий за выбранный период не найдено</p>
          </div>
        ) : (
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase whitespace-nowrap">Дата / Время</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Пользователь</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Действие</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Детали</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {logs.map((log, i) => {
                    const actionCls = ACTION_COLORS[log.action] ?? 'bg-gray-50 text-gray-600 border-gray-200'
                    const role = (log.metadata?.role as string) || ''
                    const roleCls = { admin: 'bg-red-100 text-red-700', employee: 'bg-sky-100 text-sky-700', auditor: 'bg-gray-100 text-gray-600', system: 'bg-gray-100 text-gray-500' }[role] ?? ''
                    return (
                      <tr key={log.id} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                        <td className="px-4 py-3 text-xs text-gray-500 font-mono whitespace-nowrap">
                          {new Date(log.created_at).toLocaleString('ru', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit', second:'2-digit' })}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5">
                            <User className="w-3 h-3 text-gray-400" />
                            <span className="text-sm font-medium">{log.performed_by}</span>
                            {role && <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${roleCls}`}>{role}</span>}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md border font-medium ${actionCls}`}>
                            <Activity className="w-3 h-3" />
                            {ACTION_LABELS[log.action] ?? log.action}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-500">
                            {log.metadata?.version != null && <span><span className="text-gray-400">v:</span> {String(log.metadata.version)}</span>}
                            {log.metadata?.model != null && <span><span className="text-gray-400">модель:</span> {String(log.metadata.model)}</span>}
                            {log.metadata?.duration_ms != null && <span><span className="text-gray-400">время:</span> {String(log.metadata.duration_ms)}мс</span>}
                            {log.metadata?.compliance_score != null && <span><span className="text-gray-400">GCP:</span> {String(log.metadata.compliance_score)}%</span>}
                            {log.metadata?.section != null && <span><span className="text-gray-400">секция:</span> {String(log.metadata.section)}</span>}
                            {log.metadata?.format != null && <span><span className="text-gray-400">формат:</span> {String(log.metadata.format)}</span>}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <div className="proto-audit-phdr px-4 py-3 border-t border-gray-200 text-xs text-gray-400 text-right">
              AI Protocol Generator · Напечатано: {printDate}
            </div>
          </div>
        )}
      </div>
    </>
  )
}
