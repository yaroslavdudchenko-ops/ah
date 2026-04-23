/**
 * DraftModal — полный просмотр черновика протокола.
 * Отображает все разделы активной версии в виде единого документа.
 * Поддерживает печать/PDF через window.print().
 */
import { useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { X, Printer, FileText } from 'lucide-react'
import type { ProtocolVersion } from '../api/client'

const SECTION_ORDER = [
  'title_page', 'synopsis', 'background', 'introduction',
  'objectives', 'design', 'population', 'treatment',
  'efficacy', 'safety', 'statistics', 'ethics', 'references',
]

const SECTION_LABELS: Record<string, string> = {
  title_page:   'Титульная страница',
  synopsis:     'Краткое резюме',
  background:   'Введение / Обоснование',
  introduction: 'Введение / Обоснование',
  objectives:   'Цели исследования',
  design:       'Дизайн исследования',
  population:   'Популяция',
  treatment:    'Лечение / Вмешательства',
  efficacy:     'Оценка эффективности',
  safety:       'Безопасность',
  statistics:   'Статистический анализ',
  ethics:       'Этические аспекты',
  references:   'Список литературы',
}

interface Props {
  version: ProtocolVersion
  protocolTitle: string
  onClose: () => void
}

export default function DraftModal({ version, protocolTitle, onClose }: Props) {
  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  // Prevent body scroll while open
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  const sections = SECTION_ORDER.filter(k => version.content[k])

  const handlePrint = () => window.print()

  return (
    <>
      {/* Print-only styles */}
      <style>{`
        @media print {
          body > *:not(.draft-print-root) { display: none !important; }
          .draft-print-root { position: static !important; }
          .draft-no-print { display: none !important; }
          .draft-print-body { max-height: none !important; overflow: visible !important; }
        }
      `}</style>

      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 draft-no-print"
        onClick={e => { if (e.target === e.currentTarget) onClose() }}
      >
        {/* Modal */}
        <div className="draft-print-root bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">

          {/* Header */}
          <div className="draft-no-print flex items-center justify-between px-6 py-4 border-b border-gray-200 flex-shrink-0">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-brand-600" />
              <div>
                <h2 className="font-semibold text-gray-900 text-sm leading-tight">
                  Полный черновик · v{version.version_number}
                </h2>
                <p className="text-xs text-gray-400 truncate max-w-md">{protocolTitle}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handlePrint}
                className="btn-secondary !py-1.5 !px-3 text-xs flex items-center gap-1.5"
              >
                <Printer className="w-3.5 h-3.5" />
                Печать / PDF
              </button>
              <button
                onClick={onClose}
                className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Document body */}
          <div className="draft-print-body flex-1 overflow-y-auto px-10 py-8 space-y-8">

            {/* Print header */}
            <div className="hidden print:block mb-6 pb-4 border-b border-gray-300">
              <p className="text-xs text-gray-500 text-right">
                Распечатано: {new Date().toLocaleString('ru', {
                  day: '2-digit', month: '2-digit', year: 'numeric',
                  hour: '2-digit', minute: '2-digit',
                })} · FOR RESEARCH USE ONLY — NOT FOR CLINICAL USE
              </p>
              <h1 className="text-xl font-bold text-gray-900 mt-2">{protocolTitle}</h1>
              <p className="text-sm text-gray-500">Версия {version.version_number}</p>
            </div>

            {/* Watermark */}
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 text-xs text-amber-700 text-center draft-no-print">
              FOR RESEARCH USE ONLY — NOT FOR CLINICAL USE · Черновик, требует экспертной верификации
            </div>

            {/* Sections */}
            {sections.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <FileText className="w-10 h-10 mx-auto mb-3 opacity-40" />
                <p className="text-sm">Содержимое отсутствует</p>
              </div>
            ) : sections.map((key, idx) => (
              <section key={key} className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-brand-600 bg-brand-50 rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0">
                    {idx + 1}
                  </span>
                  <h2 className="text-base font-bold text-gray-900 border-b border-gray-200 pb-1 flex-1">
                    {SECTION_LABELS[key] ?? key}
                  </h2>
                </div>
                <div className="prose prose-sm max-w-none text-gray-700 pl-9">
                  <ReactMarkdown>{version.content[key]}</ReactMarkdown>
                </div>
              </section>
            ))}

            {/* Print footer */}
            <div className="hidden print:block mt-8 pt-4 border-t border-gray-300 text-xs text-gray-400 text-center">
              Synthia AI Protocol Generator · FOR RESEARCH USE ONLY — NOT FOR CLINICAL USE
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
