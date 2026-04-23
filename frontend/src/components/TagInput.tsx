import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { X } from 'lucide-react'

// Deterministic color palette based on tag text hash — same tag = same color always
const TAG_PALETTES = [
  { bg: 'bg-blue-100',   text: 'text-blue-700',   ring: 'ring-blue-300' },
  { bg: 'bg-violet-100', text: 'text-violet-700',  ring: 'ring-violet-300' },
  { bg: 'bg-emerald-100',text: 'text-emerald-700', ring: 'ring-emerald-300' },
  { bg: 'bg-amber-100',  text: 'text-amber-700',   ring: 'ring-amber-300' },
  { bg: 'bg-rose-100',   text: 'text-rose-700',    ring: 'ring-rose-300' },
  { bg: 'bg-sky-100',    text: 'text-sky-700',     ring: 'ring-sky-300' },
  { bg: 'bg-indigo-100', text: 'text-indigo-700',  ring: 'ring-indigo-300' },
  { bg: 'bg-teal-100',   text: 'text-teal-700',    ring: 'ring-teal-300' },
]

export function tagColor(tag: string) {
  let hash = 0
  for (let i = 0; i < tag.length; i++) {
    hash = (hash * 31 + tag.charCodeAt(i)) | 0
  }
  return TAG_PALETTES[Math.abs(hash) % TAG_PALETTES.length]
}

interface Props {
  value: string[]
  onChange: (tags: string[]) => void
  suggestions?: string[]
  placeholder?: string
  disabled?: boolean
  maxTags?: number
}

export default function TagInput({
  value,
  onChange,
  suggestions = [],
  placeholder = 'Добавить тег…',
  disabled = false,
  maxTags = 20,
}: Props) {
  const [input, setInput] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)
  const [highlighted, setHighlighted] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const trimmed = input.trim()

  const filtered = trimmed.length > 0
    ? suggestions.filter(s =>
        s.toLowerCase().includes(trimmed.toLowerCase()) && !value.includes(s)
      ).slice(0, 8)
    : suggestions.filter(s => !value.includes(s)).slice(0, 8)

  const addTag = (tag: string) => {
    const clean = tag.trim().replace(/,+$/, '').trim()
    if (!clean || value.includes(clean) || value.length >= maxTags) return
    onChange([...value, clean])
    setInput('')
    setShowDropdown(false)
    inputRef.current?.focus()
  }

  const removeTag = (tag: string) => {
    onChange(value.filter(t => t !== tag))
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      if (showDropdown && filtered[highlighted]) {
        addTag(filtered[highlighted])
      } else if (trimmed) {
        addTag(trimmed)
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlighted(h => Math.min(h + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlighted(h => Math.max(h - 1, 0))
    } else if (e.key === 'Escape') {
      setShowDropdown(false)
    } else if (e.key === 'Backspace' && !input && value.length > 0) {
      removeTag(value[value.length - 1])
    }
  }

  useEffect(() => {
    setHighlighted(0)
  }, [input])

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div ref={containerRef} className="relative">
      <div
        className={`flex flex-wrap gap-1.5 min-h-[42px] px-3 py-2 rounded-lg border bg-white transition-colors cursor-text ${
          disabled ? 'bg-gray-50 border-gray-200' : 'border-gray-300 focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-100'
        }`}
        onClick={() => !disabled && inputRef.current?.focus()}
      >
        {value.map(tag => {
          const c = tagColor(tag)
          return (
            <span
              key={tag}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium ${c.bg} ${c.text} ring-1 ${c.ring}`}
            >
              {tag}
              {!disabled && (
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); removeTag(tag) }}
                  className="hover:opacity-70 transition-opacity leading-none"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </span>
          )
        })}
        {!disabled && value.length < maxTags && (
          <input
            ref={inputRef}
            value={input}
            onChange={e => {
              setInput(e.target.value)
              setShowDropdown(true)
            }}
            onFocus={() => setShowDropdown(true)}
            onKeyDown={handleKeyDown}
            placeholder={value.length === 0 ? placeholder : ''}
            className="flex-1 min-w-[120px] outline-none text-sm text-gray-700 bg-transparent placeholder:text-gray-400"
          />
        )}
      </div>

      {/* Dropdown */}
      {showDropdown && !disabled && filtered.length > 0 && (
        <div className="absolute z-50 left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden">
          {filtered.map((s, i) => {
            const c = tagColor(s)
            return (
              <button
                key={s}
                type="button"
                onMouseDown={() => addTag(s)}
                className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition-colors ${
                  i === highlighted ? 'bg-gray-100' : 'hover:bg-gray-50'
                }`}
              >
                <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${c.bg} ${c.text}`}>
                  {s}
                </span>
              </button>
            )
          })}
          {trimmed && !suggestions.some(s => s.toLowerCase() === trimmed.toLowerCase()) && (
            <button
              type="button"
              onMouseDown={() => addTag(trimmed)}
              className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition-colors ${
                highlighted === filtered.length ? 'bg-gray-100' : 'hover:bg-gray-50'
              }`}
            >
              <span className="text-gray-500">Создать тег</span>
              <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${tagColor(trimmed).bg} ${tagColor(trimmed).text}`}>
                {trimmed}
              </span>
            </button>
          )}
        </div>
      )}
      <p className="mt-1 text-xs text-gray-400">
        Введите тег и нажмите Enter или запятую. Можно выбрать из существующих.
      </p>
    </div>
  )
}
