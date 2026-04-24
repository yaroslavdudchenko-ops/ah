import type { FC } from 'react'

const MAP: Record<string, { label: string; cls: string }> = {
  draft:      { label: 'Черновик',    cls: 'bg-gray-100 text-gray-700' },
  generating: { label: 'Генерация',   cls: 'bg-blue-100 text-blue-700 animate-pulse' },
  generated:  { label: 'Сгенерирован', cls: 'bg-emerald-100 text-emerald-700' },
  approved:   { label: 'Одобрен',     cls: 'bg-teal-100 text-teal-700' },
  archived:   { label: 'В архиве',    cls: 'bg-amber-100 text-amber-700' },
  retired:    { label: 'Выведен',     cls: 'bg-gray-200 text-gray-500' },
  error:      { label: 'Ошибка',      cls: 'bg-red-100 text-red-700' },
}

const StatusBadge: FC<{ status: string }> = ({ status }) => {
  const { label, cls } = MAP[status] ?? { label: status, cls: 'bg-gray-100 text-gray-600' }
  return <span className={`badge ${cls}`}>{label}</span>
}

export default StatusBadge
