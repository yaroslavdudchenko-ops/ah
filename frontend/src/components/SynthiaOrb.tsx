/**
 * SynthiaOrb — SVG Morphing Blob animation for AI protocol generation.
 * Variant B: organic shape morphs between three forms while an iridescent
 * gradient cycles through hues. A subtle rotating ring completes the effect.
 */

const B0 = "M 210,70 C 310,60 380,130 370,220 C 360,310 290,370 200,370 C 110,370 45,300 50,210 C 55,120 110,80 210,70 Z"
const B1 = "M 220,65 C 320,75 385,150 365,240 C 345,330 265,375 175,360 C 85,345 40,265 55,175 C 70,85 120,55 220,65 Z"
const B2 = "M 200,80 C 290,55 370,125 375,205 C 380,285 320,355 235,365 C 150,375 65,315 60,225 C 55,135 110,105 200,80 Z"

const MORPH_VALUES = `${B0};${B1};${B2};${B0}`
const MORPH_DUR    = "5s"
const MORPH_SPLINES = "0.45 0 0.55 1;0.45 0 0.55 1;0.45 0 0.55 1"

interface Props {
  sections_done?: number
  total_sections?: number
  regenSection?:  string | null
  sectionLabel?:  string
}

export default function SynthiaOrb({ sections_done, total_sections, regenSection, sectionLabel }: Props) {
  const isRegen  = Boolean(regenSection)
  const pct      = total_sections && total_sections > 0
    ? Math.round((sections_done ?? 0) / total_sections * 100)
    : null

  const caption = isRegen
    ? `Перегенерация: ${sectionLabel ?? regenSection}…`
    : pct !== null
      ? `Синтезирую протокол… ${sections_done}/${total_sections} разделов`
      : 'Synthia синтезирует…'

  return (
    <div className="flex flex-col items-center gap-5 py-6">
      {/* Orb */}
      <div className="synthia-orb" style={{ width: 180, height: 180 }}>
        <svg
          viewBox="0 0 420 420"
          width="180"
          height="180"
          xmlns="http://www.w3.org/2000/svg"
          aria-label="Synthia generating"
        >
          <defs>
            {/* Main iridescent gradient */}
            <radialGradient id="sg-main" cx="38%" cy="36%" r="62%">
              <stop offset="0%"   stopColor="#e879f9" />
              <stop offset="28%"  stopColor="#818cf8" />
              <stop offset="58%"  stopColor="#22d3ee" />
              <stop offset="100%" stopColor="#a78bfa" />
            </radialGradient>

            {/* Soft glow gradient — slightly offset */}
            <radialGradient id="sg-glow" cx="55%" cy="50%" r="55%">
              <stop offset="0%"   stopColor="#f0abfc" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#6366f1" stopOpacity="0"   />
            </radialGradient>

            {/* Blur filter for the glow layer */}
            <filter id="sg-blur" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="14" />
            </filter>
          </defs>

          {/* Glow corona (blurred, larger) */}
          <path
            fill="url(#sg-glow)"
            opacity="0.7"
            filter="url(#sg-blur)"
            transform="translate(210,210) scale(1.18) translate(-210,-210)"
          >
            <animate
              attributeName="d"
              values={MORPH_VALUES}
              dur={MORPH_DUR}
              repeatCount="indefinite"
              calcMode="spline"
              keySplines={MORPH_SPLINES}
            />
          </path>

          {/* Main morphing blob */}
          <path fill="url(#sg-main)" opacity="0.92">
            <animate
              attributeName="d"
              values={MORPH_VALUES}
              dur={MORPH_DUR}
              repeatCount="indefinite"
              calcMode="spline"
              keySplines={MORPH_SPLINES}
            />
          </path>

          {/* Rotating orbit ring */}
          <g className="synthia-ring">
            <ellipse
              cx="210" cy="210"
              rx="185" ry="45"
              fill="none"
              stroke="url(#sg-main)"
              strokeWidth="2"
              strokeDasharray="18 10"
              opacity="0.35"
            />
          </g>

          {/* Inner shimmer highlight */}
          <ellipse
            cx="175" cy="155"
            rx="42" ry="26"
            fill="white"
            opacity="0.18"
          />
        </svg>
      </div>

      {/* Caption */}
      <p className="text-sm font-medium text-gray-600 animate-pulse text-center max-w-xs">
        {caption}
      </p>

      {/* Progress bar (only during full generation) */}
      {!isRegen && pct !== null && (
        <div className="w-56">
          <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
            <div
              className="h-1.5 rounded-full transition-all duration-500"
              style={{
                width: `${pct}%`,
                background: 'linear-gradient(90deg, #818cf8, #22d3ee, #e879f9)',
              }}
            />
          </div>
          <p className="text-xs text-gray-400 text-center mt-1">{pct}%</p>
        </div>
      )}
    </div>
  )
}
