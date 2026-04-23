import { tagColor } from './TagInput'

interface Props {
  tag: string
  onClick?: () => void
}

export default function TagBadge({ tag, onClick }: Props) {
  const c = tagColor(tag)
  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ring-1 transition-opacity hover:opacity-80 ${c.bg} ${c.text} ${c.ring}`}
      >
        {tag}
      </button>
    )
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ring-1 ${c.bg} ${c.text} ${c.ring}`}>
      {tag}
    </span>
  )
}
