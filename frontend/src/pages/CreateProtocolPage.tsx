import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, Plus, Trash2, Info } from 'lucide-react'
import { api, type Template, type ProtocolCreate } from '../api/client'
import Spinner from '../components/Spinner'
import ErrorAlert from '../components/ErrorAlert'
import TagInput from '../components/TagInput'
import AutocompleteField from '../components/AutocompleteField'

const PHASES = [
  { value: 'I',   label: 'Фаза I' },
  { value: 'II',  label: 'Фаза II' },
  { value: 'III', label: 'Фаза III' },
  { value: 'IV',  label: 'Фаза IV' },
]

const AREAS = [
  'Онкология', 'Кардиология', 'Неврология', 'Эндокринология',
  'Пульмонология', 'Ревматология', 'Гастроэнтерология', 'Иммунология', 'Другое',
]

type ListField = 'secondary_endpoints' | 'inclusion_criteria' | 'exclusion_criteria'

interface FormState {
  title: string
  drug_name: string
  inn: string
  phase: string
  therapeutic_area: string
  indication: string
  population: string
  primary_endpoint: string
  secondary_endpoints: string[]
  duration_weeks: string
  dosing: string
  inclusion_criteria: string[]
  exclusion_criteria: string[]
  tags: string[]
  template_id: string
}

const initial: FormState = {
  title: '', drug_name: '', inn: '', phase: 'II', therapeutic_area: '',
  indication: '', population: '', primary_endpoint: '',
  secondary_endpoints: [''], duration_weeks: '24', dosing: '',
  inclusion_criteria: [''], exclusion_criteria: [''], tags: [], template_id: '',
}

export default function CreateProtocolPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState<FormState>(initial)
  const [templates, setTemplates] = useState<Template[]>([])
  const [allTags, setAllTags] = useState<string[]>([])
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({})
  const [submitting, setSubmitting] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)

  useEffect(() => {
    api.getTemplates().then(setTemplates).catch(() => {})
    api.getAllTags().then(setAllTags).catch(() => {})
  }, [])

  const set = (field: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }))

  const setList = (field: ListField, idx: number, val: string) =>
    setForm(f => {
      const arr = [...f[field]]; arr[idx] = val
      return { ...f, [field]: arr }
    })

  const addItem = (field: ListField) =>
    setForm(f => ({ ...f, [field]: [...f[field], ''] }))

  const removeItem = (field: ListField, idx: number) =>
    setForm(f => ({ ...f, [field]: f[field].filter((_, i) => i !== idx) }))

  const validate = (): boolean => {
    const e: typeof errors = {}
    if (!form.title.trim()) e.title = 'Обязательное поле'
    if (!form.drug_name.trim()) e.drug_name = 'Обязательное поле'
    if (!form.inn.trim()) e.inn = 'Обязательное поле'
    if (!form.therapeutic_area) e.therapeutic_area = 'Выберите терапевтическую область'
    if (form.indication.trim().length < 10) e.indication = 'Минимум 10 символов'
    if (form.population.trim().length < 10) e.population = 'Минимум 10 символов'
    if (form.primary_endpoint.trim().length < 10) e.primary_endpoint = 'Минимум 10 символов'
    if (form.dosing.trim().length < 5) e.dosing = 'Минимум 5 символов'
    const weeks = Number(form.duration_weeks)
    if (!weeks || weeks < 1 || weeks > 520) e.duration_weeks = 'Укажите корректное число недель (1–520)'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    setSubmitting(true)
    setApiError(null)
    try {
      const body: ProtocolCreate = {
        ...form,
        duration_weeks: Number(form.duration_weeks),
        secondary_endpoints: form.secondary_endpoints.filter(s => s.trim()),
        inclusion_criteria: form.inclusion_criteria.filter(s => s.trim()),
        exclusion_criteria: form.exclusion_criteria.filter(s => s.trim()),
        tags: form.tags,
        template_id: form.template_id || undefined,
      }
      const proto = await api.createProtocol(body)
      navigate(`/protocols/${proto.id}`)
    } catch (err) {
      setApiError((err as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <button onClick={() => navigate('/protocols')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6">
        <ChevronLeft className="w-4 h-4" /> Назад к списку
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Новый протокол</h1>
        <p className="text-sm text-gray-500 mt-1">Заполните мета-данные — AI сгенерирует все разделы протокола</p>
      </div>

      {apiError && <div className="mb-6"><ErrorAlert message={apiError} onClose={() => setApiError(null)} /></div>}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Template */}
        {templates.length > 0 && (
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-3">
              <h2 className="font-semibold text-gray-900">Шаблон (опционально)</h2>
              <Info className="w-4 h-4 text-gray-400" />
            </div>
            <select className="form-input" value={form.template_id} onChange={set('template_id')}>
              <option value="">— Без шаблона (стандартная структура ICH E6) —</option>
              {templates.map(t => (
                <option key={t.id} value={t.id}>{t.name} · {t.phase}</option>
              ))}
            </select>
          </div>
        )}

        {/* Basic info */}
        <div className="card p-5 space-y-4">
          <h2 className="font-semibold text-gray-900">Основная информация</h2>

          <div>
            <label className="form-label">Название исследования *</label>
            <input className="form-input" value={form.title} onChange={set('title')}
              placeholder="Двойное слепое РКИ BCD-100 при меланоме..." />
            {errors.title && <p className="form-error">{errors.title}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="form-label">МНН (INN) *</label>
              <AutocompleteField
                field="inn"
                value={form.inn}
                onChange={v => setForm(f => ({ ...f, inn: v }))}
                placeholder="пролголимаб"
              />
              {errors.inn && <p className="form-error">{errors.inn}</p>}
            </div>
            <div>
              <label className="form-label">Торговое наименование *</label>
              <AutocompleteField
                field="drug_name"
                value={form.drug_name}
                onChange={v => setForm(f => ({ ...f, drug_name: v }))}
                placeholder="BCD-100"
              />
              {errors.drug_name && <p className="form-error">{errors.drug_name}</p>}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="form-label">Фаза *</label>
              <select className="form-input" value={form.phase} onChange={set('phase')}>
                {PHASES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </div>
            <div>
              <label className="form-label">Терапевтическая область *</label>
              <select className="form-input" value={form.therapeutic_area} onChange={set('therapeutic_area')}>
                <option value="">Выберите...</option>
                {AREAS.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
              {errors.therapeutic_area && <p className="form-error">{errors.therapeutic_area}</p>}
            </div>
          </div>
        </div>

        {/* Study design */}
        <div className="card p-5 space-y-4">
          <h2 className="font-semibold text-gray-900">Дизайн исследования</h2>

          <div>
            <label className="form-label">Показание / Нозология *</label>
            <AutocompleteField
              field="indication"
              value={form.indication}
              onChange={v => setForm(f => ({ ...f, indication: v }))}
              placeholder="Нерезектабельная или метастатическая меланома кожи, не получавшая ранее иммунотерапии..."
              multiline rows={3}
            />
            {errors.indication && <p className="form-error">{errors.indication}</p>}
          </div>

          <div>
            <label className="form-label">Популяция пациентов *</label>
            <AutocompleteField
              field="population"
              value={form.population}
              onChange={v => setForm(f => ({ ...f, population: v }))}
              placeholder="Взрослые пациенты ≥18 лет с подтверждённым гистологически диагнозом..."
              multiline rows={3}
            />
            {errors.population && <p className="form-error">{errors.population}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="form-label">Режим дозирования *</label>
              <AutocompleteField
                field="dosing"
                value={form.dosing}
                onChange={v => setForm(f => ({ ...f, dosing: v }))}
                placeholder="1 мг/кг в/в каждые 2 недели"
              />
              {errors.dosing && <p className="form-error">{errors.dosing}</p>}
            </div>
            <div>
              <label className="form-label">Длительность (недели) *</label>
              <input type="number" className="form-input" value={form.duration_weeks}
                onChange={set('duration_weeks')} min={1} max={520} />
              {errors.duration_weeks && <p className="form-error">{errors.duration_weeks}</p>}
            </div>
          </div>
        </div>

        {/* Endpoints */}
        <div className="card p-5 space-y-4">
          <h2 className="font-semibold text-gray-900">Конечные точки</h2>

          <div>
            <label className="form-label">Первичная конечная точка *</label>
            <AutocompleteField
              field="primary_endpoint"
              value={form.primary_endpoint}
              onChange={v => setForm(f => ({ ...f, primary_endpoint: v }))}
              placeholder="Общая выживаемость (OS) — время от рандомизации до смерти по любой причине..."
              multiline rows={3}
            />
            {errors.primary_endpoint && <p className="form-error">{errors.primary_endpoint}</p>}
          </div>

          <div>
            <label className="form-label">Вторичные конечные точки</label>
            <div className="space-y-2">
              {form.secondary_endpoints.map((ep, i) => (
                <div key={i} className="flex gap-2">
                  <input className="form-input" value={ep}
                    onChange={e => setList('secondary_endpoints', i, e.target.value)}
                    placeholder={`Конечная точка ${i + 1}`} />
                  {form.secondary_endpoints.length > 1 && (
                    <button type="button" onClick={() => removeItem('secondary_endpoints', i)}
                      className="p-2 text-gray-400 hover:text-red-500">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
              <button type="button" onClick={() => addItem('secondary_endpoints')}
                className="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700">
                <Plus className="w-3.5 h-3.5" /> Добавить
              </button>
            </div>
          </div>
        </div>

        {/* Criteria */}
        <div className="card p-5 space-y-4">
          <h2 className="font-semibold text-gray-900">Критерии отбора</h2>

          <CriteriaList label="Критерии включения" items={form.inclusion_criteria}
            onChange={(i, v) => setList('inclusion_criteria', i, v)}
            onAdd={() => addItem('inclusion_criteria')}
            onRemove={(i) => removeItem('inclusion_criteria', i)} />

          <CriteriaList label="Критерии исключения" items={form.exclusion_criteria}
            onChange={(i, v) => setList('exclusion_criteria', i, v)}
            onAdd={() => addItem('exclusion_criteria')}
            onRemove={(i) => removeItem('exclusion_criteria', i)} />
        </div>

        {/* Tags */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-900 mb-1">Теги</h2>
          <p className="text-sm text-gray-500 mb-3">Метки для классификации и быстрого поиска (например: GCP-review, Онкология, Срочно)</p>
          <TagInput
            value={form.tags}
            onChange={tags => setForm(f => ({ ...f, tags }))}
            suggestions={allTags}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pb-8">
          <button type="button" onClick={() => navigate('/protocols')} className="btn-secondary">
            Отмена
          </button>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? <><Spinner size={16} /> Создание...</> : 'Создать протокол'}
          </button>
        </div>
      </form>
    </div>
  )
}

interface CriteriaListProps {
  label: string
  items: string[]
  onChange: (i: number, v: string) => void
  onAdd: () => void
  onRemove: (i: number) => void
}

function CriteriaList({ label, items, onChange, onAdd, onRemove }: CriteriaListProps) {
  return (
    <div>
      <label className="form-label">{label}</label>
      <div className="space-y-2">
        {items.map((item, i) => (
          <div key={i} className="flex gap-2 items-start">
            <span className="w-5 h-5 flex-shrink-0 flex items-center justify-center mt-2 text-xs text-gray-400 font-medium">{i + 1}.</span>
            <input className="form-input" value={item} onChange={e => onChange(i, e.target.value)}
              placeholder="Критерий..." />
            {items.length > 1 && (
              <button type="button" onClick={() => onRemove(i)}
                className="p-2 mt-0.5 text-gray-400 hover:text-red-500">
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        ))}
        <button type="button" onClick={onAdd}
          className="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700">
          <Plus className="w-3.5 h-3.5" /> Добавить
        </button>
      </div>
    </div>
  )
}
