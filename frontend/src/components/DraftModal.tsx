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
          @page {
            size: A4 portrait;
            margin: 22mm 18mm 18mm 18mm;
          }

          * {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }

          body > *:not(.draft-print-root) { display: none !important; }
          .draft-print-root {
            position: static !important;
            background: #fff !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            max-width: 100% !important;
            width: 100% !important;
          }
          .draft-no-print { display: none !important; }
          .draft-print-body {
            max-height: none !important;
            overflow: visible !important;
            padding: 0 !important;
          }

          /* Section page breaks */
          .draft-print-section {
            break-inside: avoid-page;
            page-break-inside: avoid;
          }
          .draft-print-section + .draft-print-section {
            break-before: auto;
            page-break-before: auto;
          }

          /* Section header accent */
          .draft-print-section-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
            padding-bottom: 6px;
            border-bottom: 2px solid #0284c7 !important;
          }
          .draft-print-section-num {
            background: #0284c7 !important;
            color: #fff !important;
            border-radius: 50%;
            width: 22px;
            height: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 700;
            flex-shrink: 0;
          }
          .draft-print-section-title {
            font-size: 13px;
            font-weight: 700;
            color: #0c4a6e !important;
          }

          /* Prose reset for print */
          .draft-print-body h1 { font-size: 18px; font-weight: 700; color: #0c4a6e !important; margin: 16px 0 6px; }
          .draft-print-body h2 { font-size: 14px; font-weight: 600; color: #0369a1 !important; margin: 12px 0 4px; }
          .draft-print-body h3 { font-size: 12px; font-weight: 600; color: #374151; margin: 10px 0 4px; }
          .draft-print-body p  { font-size: 11px; line-height: 1.65; color: #111827; margin: 0 0 6px; }
          .draft-print-body ul, .draft-print-body ol { margin: 4px 0 8px 16px; }
          .draft-print-body li { font-size: 11px; line-height: 1.6; color: #111827; }
          .draft-print-body strong { color: #0c4a6e !important; }
          .draft-print-body blockquote {
            border-left: 3px solid #0284c7 !important;
            background: #f0f9ff !important;
            padding: 6px 10px;
            margin: 8px 0;
            font-size: 11px;
            color: #374151;
          }
          .draft-print-body table { border-collapse: collapse; width: 100%; font-size: 10px; }
          .draft-print-body th {
            background: #0284c7 !important;
            color: #fff !important;
            padding: 5px 8px;
            text-align: left;
            font-weight: 600;
          }
          .draft-print-body td { border: 1px solid #e5e7eb !important; padding: 4px 8px; }
          .draft-print-body tr:nth-child(even) td { background: #f8faff !important; }

          /* Print header */
          .draft-print-header-bar {
            border-bottom: 3px solid #0284c7 !important;
            padding-bottom: 10px;
            margin-bottom: 20px;
          }
          .draft-print-header-bar h1 {
            font-size: 20px;
            font-weight: 800;
            color: #0c4a6e !important;
            margin: 6px 0 2px;
          }
          .draft-print-header-bar p {
            font-size: 11px;
            color: #6b7280;
            margin: 2px 0;
          }
          .draft-print-header-meta {
            font-size: 10px;
            color: #9ca3af;
            text-align: right;
          }
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
            <div className="hidden print:block draft-print-header-bar">
              <p className="draft-print-header-meta">
                Распечатано: {new Date().toLocaleString('ru', {
                  day: '2-digit', month: '2-digit', year: 'numeric',
                  hour: '2-digit', minute: '2-digit',
                })} · FOR RESEARCH USE ONLY — NOT FOR CLINICAL USE
              </p>
              <h1>{protocolTitle}</h1>
              <p>Версия {version.version_number}</p>
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
              <section key={key} className="space-y-3 draft-print-section">
                <div className="flex items-center gap-3 draft-print-section-header">
                  <span className="text-xs font-bold text-brand-600 bg-brand-50 rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 draft-print-section-num">
                    {idx + 1}
                  </span>
                  <h2 className="text-base font-bold text-gray-900 border-b border-gray-200 pb-1 flex-1 draft-print-section-title">
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
