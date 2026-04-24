/**
 * AutocompleteField — field with suggestions from existing protocol data.
 *
 * Designed with RAG extensibility:
 * - `suggestionProvider` is injectable (default: API call to /suggestions)
 * - When RAG is enabled, swap `suggestionProvider` for an embedding-based call
 *   without changing this component's interface.
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import { api } from '../api/client'

export type SuggestionProvider = (field: string, q: string) => Promise<string[]>

const defaultProvider: SuggestionProvider = (field, q) =>
  api.getFieldSuggestions(field, q)

interface AutocompleteFieldProps {
  /** Protocol field name for the backend suggestions endpoint */
  field: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  multiline?: boolean
  rows?: number
  className?: string
  disabled?: boolean
  /** Swap for RAG-based provider when available */
  suggestionProvider?: SuggestionProvider
}

export default function AutocompleteField({
  field,
  value,
  onChange,
  placeholder,
  multiline = false,
  rows = 2,
  className = 'form-input',
  disabled = false,
  suggestionProvider = defaultProvider,
}: AutocompleteFieldProps) {
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  const fetchSuggestions = useCallback(
    (q: string) => {
      clearTimeout(debounceRef.current)
      if (q.trim().length < 2) { setSuggestions([]); return }
      debounceRef.current = setTimeout(async () => {
        try {
          const results = await suggestionProvider(field, q)
          // Filter out exact match to avoid noise
          setSuggestions(results.filter(r => r !== q).slice(0, 8))
        } catch {
          setSuggestions([])
        }
      }, 280)
    },
    [field, suggestionProvider],
  )

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    onChange(e.target.value)
    fetchSuggestions(e.target.value)
    setShowDropdown(true)
  }

  const handleSelect = (val: string) => {
    onChange(val)
    setSuggestions([])
    setShowDropdown(false)
  }

  const sharedProps = {
    className: `${className} w-full`,
    value,
    onChange: handleChange,
    onFocus: () => { if (suggestions.length) setShowDropdown(true) },
    onBlur: () => setTimeout(() => setShowDropdown(false), 120),
    placeholder,
    disabled,
  }

  return (
    <div ref={containerRef} className="relative">
      {multiline ? (
        <textarea {...sharedProps} rows={rows} style={{ resize: 'none' }} />
      ) : (
        <input {...sharedProps} type="text" />
      )}

      {showDropdown && suggestions.length > 0 && (
        <ul className="absolute z-30 left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden text-sm">
          {suggestions.map((s, i) => (
            <li key={i}>
              <button
                type="button"
                onMouseDown={e => { e.preventDefault(); handleSelect(s) }}
                className="w-full text-left px-3 py-2 text-gray-700 hover:bg-brand-50 hover:text-brand-700 truncate transition-colors"
                title={s}
              >
                {s}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
