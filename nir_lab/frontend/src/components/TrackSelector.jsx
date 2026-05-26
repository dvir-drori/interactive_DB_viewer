/**
 * components/TrackSelector.jsx
 * Left sidebar panel for toggling individual tracks on/off, grouped by category.
 * Passes the set of active labels back to the parent via onChange().
 */

const CATEGORY_COLORS = {
  'Lab Data':       'text-lab-accent',
  'Biopsies':       'text-lab-biopsy',
  'Plasma Samples': 'text-lab-plasma',
}

// Labels that belong to ChIP-seq (epigenomic) data
const CHIPSEQ_LABELS = ['H3K4me3', 'H3K27ac', 'H3K27me3', 'H3K9me3']

export default function TrackSelector({ labelsByCategory, activeLabels, onChange }) {
  if (!labelsByCategory) return null

  function toggleLabel(label) {
    const next = new Set(activeLabels)
    next.has(label) ? next.delete(label) : next.add(label)
    onChange(next)
  }

  function toggleAll(labels, enable) {
    const next = new Set(activeLabels)
    labels.forEach(l => enable ? next.add(l) : next.delete(l))
    onChange(next)
  }

  const categories = Object.entries(labelsByCategory)

  return (
    <div className="w-56 shrink-0 bg-lab-panel border-r border-lab-border overflow-y-auto p-3 space-y-5">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Tracks</h2>

      {categories.map(([category, labels]) => {
        const allOn  = labels.every(l => activeLabels.has(l))
        const isChip = category === 'Plasma Samples'
        const colorClass = CATEGORY_COLORS[category] || 'text-gray-300'

        return (
          <div key={category}>
            {/* Category header */}
            <div className="flex items-center justify-between mb-1">
              <span className={`text-xs font-semibold uppercase tracking-wide ${colorClass}`}>
                {isChip ? '⬡ Epigenomics' : category}
              </span>
              <button
                onClick={() => toggleAll(labels, !allOn)}
                className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
              >
                {allOn ? 'none' : 'all'}
              </button>
            </div>

            {/* Individual label checkboxes */}
            <div className="space-y-1">
              {labels.map(label => {
                const isChipSeq = CHIPSEQ_LABELS.includes(label)
                return (
                  <label
                    key={label}
                    className="flex items-center gap-2 cursor-pointer group"
                  >
                    <input
                      type="checkbox"
                      checked={activeLabels.has(label)}
                      onChange={() => toggleLabel(label)}
                      className="accent-lab-accent shrink-0"
                    />
                    <span className={`text-xs truncate group-hover:text-white transition-colors ${
                      isChipSeq ? 'text-purple-400 font-medium' : 'text-gray-400'
                    }`}>
                      {label}
                    </span>
                    {isChipSeq && (
                      <span className="text-xs bg-purple-900/40 text-purple-300 px-1 rounded ml-auto shrink-0">
                        ChIP
                      </span>
                    )}
                  </label>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
