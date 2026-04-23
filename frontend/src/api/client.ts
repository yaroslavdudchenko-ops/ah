const BASE = '/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: { message: res.statusText } }))
    throw new Error(err?.error?.message || err?.detail || res.statusText)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  // Templates
  getTemplates: () => request<Template[]>('/templates'),

  // Protocols
  listProtocols: (params?: { limit?: number; offset?: number; phase?: string }) => {
    const q = new URLSearchParams()
    if (params?.limit) q.set('limit', String(params.limit))
    if (params?.offset) q.set('offset', String(params.offset))
    if (params?.phase) q.set('phase', params.phase)
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
  startGenerate: (id: string) =>
    request<{ task_id: string; status: string }>(`/protocols/${id}/generate`, { method: 'POST', body: '{}' }),
  getGenerateStatus: (id: string, taskId: string) =>
    request<GenerateStatus>(`/protocols/${id}/generate/${taskId}`),

  // Check
  checkConsistency: (id: string) =>
    request<CheckResponse>(`/protocols/${id}/check`, { method: 'POST', body: '{}' }),

  // Export
  exportProtocol: async (id: string, format: 'md' | 'html' | 'docx') => {
    const res = await fetch(`${BASE}/protocols/${id}/export?format=${format}`)
    if (!res.ok) throw new Error('Export failed')
    const blob = await res.blob()
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
  phase: string
  status: string
  updated_at: string
}

export interface ProtocolVersion {
  id: string
  protocol_id: string
  version_number: number
  content: Record<string, string>
  compliance_score?: number
  generated_by: string
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

export interface CheckResponse {
  compliance_score: number
  rf_compliance_score: number
  issues: IssueItem[]
  summary: string
  rf_summary: string
}
