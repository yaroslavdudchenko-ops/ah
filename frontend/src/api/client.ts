const BASE = '/api/v1'
const STORAGE_KEY = 'ai_proto_auth'

function getToken(): string | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw).token : null
  } catch {
    return null
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, { ...options, headers })

  if (res.status === 401) {
    localStorage.removeItem(STORAGE_KEY)
    window.location.href = '/login'
    throw new Error('Session expired')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: { message: res.statusText } }))
    const msg = err?.detail?.error?.message || err?.error?.message || err?.detail || res.statusText
    throw new Error(msg)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

async function requestBlob(path: string): Promise<Blob> {
  const token = getToken()
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${BASE}${path}`, { headers })
  if (!res.ok) throw new Error('Export failed')
  return res.blob()
}

export const api = {
  // Templates
  getTemplates: () => request<Template[]>('/templates'),

  // Protocols
  listProtocols: (params?: {
    limit?: number; offset?: number;
    phase?: string; tag?: string;
    status?: string; therapeutic_area?: string; search?: string;
  }) => {
    const q = new URLSearchParams()
    if (params?.limit) q.set('limit', String(params.limit))
    if (params?.offset) q.set('offset', String(params.offset))
    if (params?.phase) q.set('phase', params.phase)
    if (params?.tag) q.set('tag', params.tag)
    if (params?.status) q.set('status', params.status)
    if (params?.therapeutic_area) q.set('therapeutic_area', params.therapeutic_area)
    if (params?.search) q.set('search', params.search)
    return request<ProtocolListItem[]>(`/protocols?${q}`)
  },
  createProtocol: (body: ProtocolCreate) =>
    request<Protocol>('/protocols', { method: 'POST', body: JSON.stringify(body) }),
  getProtocol: (id: string) => request<Protocol>(`/protocols/${id}`),
  updateProtocol: (id: string, body: Partial<Protocol>) =>
    request<Protocol>(`/protocols/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteProtocol: (id: string) => request<void>(`/protocols/${id}`, { method: 'DELETE' }),

  // Versions
  listVersions: (id: string) => request<ProtocolVersion[]>(`/protocols/${id}/versions`),

  // Generate
  startGenerate: (id: string, comment?: string) =>
    request<{ task_id: string; status: string }>(`/protocols/${id}/generate`, {
      method: 'POST',
      body: JSON.stringify({ comment }),
    }),
  getGenerateStatus: (id: string, taskId: string) =>
    request<GenerateStatus>(`/protocols/${id}/generate/${taskId}`),

  // Section regenerate (FR-03.5)
  regenerateSection: (id: string, sectionKey: string) =>
    request<{ task_id: string; section: string }>(
      `/protocols/${id}/sections/${sectionKey}/regenerate`,
      { method: 'POST' }
    ),

  // Check
  checkConsistency: (id: string) =>
    request<CheckResponse>(`/protocols/${id}/check`, { method: 'POST', body: '{}' }),

  // Tags
  getAllTags: () => request<string[]>('/tags'),

  // Audit Trail
  listAuditLog: (params?: { from_date?: string; to_date?: string; action?: string; performed_by?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams()
    if (params?.from_date)    q.set('from_date', params.from_date)
    if (params?.to_date)      q.set('to_date', params.to_date)
    if (params?.action)       q.set('action', params.action)
    if (params?.performed_by) q.set('performed_by', params.performed_by)
    if (params?.limit)        q.set('limit', String(params.limit))
    if (params?.offset)       q.set('offset', String(params.offset))
    return request<AuditEntry[]>(`/audit-log?${q}`)
  },
  listProtocolAudit: (id: string, params?: { from_date?: string; to_date?: string }) => {
    const q = new URLSearchParams()
    if (params?.from_date) q.set('from_date', params.from_date)
    if (params?.to_date)   q.set('to_date', params.to_date)
    return request<AuditEntry[]>(`/protocols/${id}/audit?${q}`)
  },

  // Export
  exportProtocol: async (id: string, format: 'md' | 'html' | 'docx') => {
    const blob = await requestBlob(`/protocols/${id}/export?format=${format}`)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const ext = format === 'html' ? 'html' : format === 'docx' ? 'docx' : 'md'
    a.download = `protocol_${id.slice(0, 8)}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  },
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface Template {
  id: string
  name: string
  phase: string
  design_type: string
  description?: string
}

export interface ProtocolCreate {
  title: string
  drug_name: string
  inn: string
  phase: string
  therapeutic_area: string
  indication: string
  population: string
  primary_endpoint: string
  secondary_endpoints: string[]
  duration_weeks: number
  dosing: string
  inclusion_criteria: string[]
  exclusion_criteria: string[]
  tags: string[]
  template_id?: string
}

export interface Protocol extends ProtocolCreate {
  id: string
  status: string
  created_at: string
  updated_at: string
}

export interface ProtocolListItem {
  id: string
  title: string
  drug_name: string
  inn?: string
  phase: string
  status: string
  therapeutic_area?: string
  tags: string[]
  updated_at: string
  created_at?: string
}

export interface ProtocolVersion {
  id: string
  protocol_id: string
  version_number: number
  content: Record<string, string>
  comment?: string
  compliance_score?: number
  generated_by: string
  is_archived: boolean
  created_at: string
}

export interface GenerateStatus {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  sections_done: number
  total_sections: number
  message?: string
}

export interface IssueItem {
  type: string
  severity: 'high' | 'medium' | 'low'
  section: string
  description: string
  suggestion?: string
}

export interface AuditEntry {
  id: string
  entity_type: string
  entity_id: string
  action: string
  performed_by: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface CheckResponse {
  compliance_score: number
  rf_compliance_score: number
  issues: IssueItem[]
  summary: string
  rf_summary: string
}
