/**
 * components/ChipSeqTrack.jsx
 * Heatmap visualization for ChIP-seq tracks (H3K4me3 and similar epigenomic markers).
 *
 * Renders as a Plotly heatmap where:
 *   x-axis = day offset (days since transplant)
 *   y-axis = label name (one row per ChIP-seq marker)
 *   color  = enrichment level (1=low, 2=moderate, 3=high)
 *
 * Color scale: white → light blue → dark blue → deep purple
 * representing increasing ChIP-seq signal enrichment.
 */
import Plot from 'react-plotly.js'

// Human-readable enrichment level descriptions
const LEVEL_LABELS = {
  '1': 'Low enrichment',
  '2': 'Moderate enrichment',
  '3': 'High enrichment',
}

// Color scale: 0 = no signal (bg), 1 = low, 2 = moderate, 3 = high
const COLOR_SCALE = [
  [0,   '#1a1d27'],   // background (no data)
  [0.1, '#c7d2fe'],   // level 1 — light blue/indigo
  [0.5, '#4338ca'],   // level 2 — medium purple
  [1.0, '#7c3aed'],   // level 3 — deep violet
]

export default function ChipSeqTrack({ measurements, patientId, totalDays }) {
  if (!measurements || measurements.length === 0) return null

  // Group measurements by label
  const byLabel = {}
  for (const m of measurements) {
    if (!byLabel[m.label]) byLabel[m.label] = {}
    const val = parseFloat(m.value)
    if (!isNaN(val)) {
      byLabel[m.label][m.day_offset] = val
    }
  }

  const labels   = Object.keys(byLabel)
  const days     = Array.from({ length: totalDays }, (_, i) => i + 1)

  // Build z matrix: rows = labels, columns = days
  const z = labels.map(label =>
    days.map(day => byLabel[label][day] ?? null)
  )

  // Tooltip text matrix
  const text = labels.map((label, li) =>
    days.map(day => {
      const val = z[li][days.indexOf(day)]
      if (val === null) return ''
      const levelDesc = LEVEL_LABELS[String(Math.round(val))] || `Level ${val}`
      return `${label}<br>Day ${day}<br>${levelDesc}`
    })
  )

  return (
    <div className="mt-2">
      {/* Section header */}
      <div className="flex items-center gap-3 mb-2 px-2">
        <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">
          ⬡ Epigenomic Markers (ChIP-seq)
        </span>
        {/* Legend */}
        <div className="flex items-center gap-3 ml-4">
          {Object.entries(LEVEL_LABELS).map(([val, desc]) => (
            <div key={val} className="flex items-center gap-1">
              <div
                className="w-3 h-3 rounded-sm"
                style={{ background: val === '1' ? '#c7d2fe' : val === '2' ? '#4338ca' : '#7c3aed' }}
              />
              <span className="text-xs text-gray-400">{desc}</span>
            </div>
          ))}
        </div>
      </div>

      <Plot
        data={[
          {
            type:        'heatmap',
            z,
            x:           days,
            y:           labels,
            text,
            hoverinfo:   'text',
            colorscale:  COLOR_SCALE,
            zmin:        0,
            zmax:        3,
            showscale:   false,
            xgap:        1,
            ygap:        2,
          },
        ]}
        layout={{
          height:      Math.max(80, labels.length * 50),
          margin:      { t: 10, b: 30, l: 100, r: 20 },
          paper_bgcolor: 'transparent',
          plot_bgcolor:  'transparent',
          xaxis: {
            title:     'Day since transplant',
            color:     '#9ca3af',
            gridcolor: '#2a2d3e',
            range:     [0, totalDays + 1],
          },
          yaxis: {
            color:    '#9ca3af',
            tickfont: { size: 11 },
          },
          font: { color: '#9ca3af', size: 11 },
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%' }}
      />
    </div>
  )
}
