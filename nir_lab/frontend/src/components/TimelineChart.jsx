/**
 * components/TimelineChart.jsx
 * Main multi-track Plotly chart for a single patient.
 *
 * Layout: vertically stacked subplots sharing the x-axis (day offset).
 *   Subplot 1 — Lab Data: one line per selected label, continuous values
 *   Subplot 2 — Clinical Events: scatter/lollipop plot, one row per label
 *
 * ChIP-seq tracks are rendered separately by ChipSeqTrack.jsx (heatmap).
 *
 * X-axis shows both day offset (primary) and calendar date (secondary ticks).
 */
import Plot from 'react-plotly.js'

const LAB_COLORS = [
  '#4f8ef7','#f59e0b','#10b981','#ef4444','#8b5cf6',
  '#06b6d4','#f97316','#84cc16','#ec4899','#14b8a6',
  '#a78bfa','#fb923c','#34d399','#f472b6','#60a5fa',
]

function colorForIndex(i) {
  return LAB_COLORS[i % LAB_COLORS.length]
}

export default function TimelineChart({ labData, events, notes, totalDays, firstDate }) {
  if (!labData && !events) return null

  // ------------------------------------------------------------------ //
  // Build date tick labels: map day_offset → calendar date string
  // ------------------------------------------------------------------ //
  function dayToDate(dayOffset) {
    if (!firstDate) return `Day ${dayOffset}`
    const d = new Date(firstDate)
    d.setDate(d.getDate() + dayOffset - 1)
    return d.toISOString().split('T')[0]
  }

  // ------------------------------------------------------------------ //
  // Subplot 1: Lab Data lines
  // ------------------------------------------------------------------ //
  const labTraces = []
  const labLabels = [...new Set((labData || []).map(m => m.label))]

  labLabels.forEach((label, i) => {
    const pts = (labData || [])
      .filter(m => m.label === label)
      .sort((a, b) => a.day_offset - b.day_offset)

    labTraces.push({
      type:    'scatter',
      mode:    'lines+markers',
      name:    label,
      x:       pts.map(p => p.day_offset),
      y:       pts.map(p => parseFloat(p.value)),
      line:    { color: colorForIndex(i), width: 1.5 },
      marker:  { size: 5, color: colorForIndex(i) },
      hovertemplate:
        `<b>${label}</b><br>Day %{x} (${dayToDate('%{x}')})<br>Value: %{y}<extra></extra>`,
      xaxis: 'x',
      yaxis: `y${i + 1}`,   // each lab track gets its own y-axis
    })
  })

  // ------------------------------------------------------------------ //
  // Subplot 2: Clinical Events (lollipop scatter)
  // ------------------------------------------------------------------ //
  const eventLabels = [...new Set((events || []).map(e => e.label))]
  const eventTraces = eventLabels.map((label, i) => {
    const pts = (events || []).filter(e => e.label === label)
    const color = label.toLowerCase().includes('biopsy') ? '#f59e0b' : '#10b981'
    return {
      type:    'scatter',
      mode:    'markers',
      name:    label,
      x:       pts.map(p => p.day_offset),
      y:       pts.map(() => label),
      marker:  { size: 10, color, symbol: 'diamond', line: { width: 1, color: '#fff' } },
      hovertemplate:
        `<b>${label}</b><br>Day %{x}<br>Value: %{customdata}<extra></extra>`,
      customdata: pts.map(p => p.value),
      xaxis:   'x',
      yaxis:   'y_events',
    }
  })

  // ------------------------------------------------------------------ //
  // Notes as vertical lines
  // ------------------------------------------------------------------ //
  const noteShapes = (notes || []).map(n => ({
    type:      'line',
    xref:      'x',
    yref:      'paper',
    x0:        n.day_offset,
    x1:        n.day_offset,
    y0:        0,
    y1:        1,
    line:      { color: '#fbbf24', width: 1, dash: 'dot' },
  }))

  const noteAnnotations = (notes || []).map(n => ({
    x:          n.day_offset,
    y:          1,
    xref:       'x',
    yref:       'paper',
    text:       '📝',
    showarrow:  false,
    font:       { size: 10 },
    xanchor:    'center',
  }))

  // ------------------------------------------------------------------ //
  // Build subplot layout: one row per lab label + one events row
  // ------------------------------------------------------------------ //
  const nLab    = labLabels.length
  const hasLab  = nLab > 0
  const hasEvt  = eventLabels.length > 0
  const nRows   = (hasLab ? nLab : 0) + (hasEvt ? 1 : 0)
  const rowH    = 120   // pixels per lab track
  const evtH    = 100   // pixels for events track
  const totalH  = nLab * rowH + (hasEvt ? evtH : 0) + 60

  // Compute y-axis domain fractions (bottom to top)
  const domains = {}
  const step    = 1 / nRows
  if (hasEvt) {
    domains['y_events'] = [0, step * 0.85]
  }
  labLabels.forEach((_, i) => {
    const base = hasEvt ? step : 0
    domains[`y${i + 1}`] = [base + i * step + 0.01, base + (i + 1) * step - 0.01]
  })

  const layoutYAxes = {}
  labLabels.forEach((label, i) => {
    layoutYAxes[`yaxis${i + 1}`] = {
      domain:     domains[`y${i + 1}`],
      title:      { text: label, font: { size: 10 }, standoff: 4 },
      color:      '#9ca3af',
      gridcolor:  '#2a2d3e',
      tickfont:   { size: 9 },
      zeroline:   false,
    }
  })

  if (hasEvt) {
    layoutYAxes['yaxis_events'] = {
      domain:     domains['y_events'],
      color:      '#9ca3af',
      gridcolor:  '#2a2d3e',
      tickfont:   { size: 9 },
      zeroline:   false,
    }
  }

  // Remap traces to correct axis names
  const allTraces = [
    ...labTraces.map((t, i) => ({ ...t, yaxis: i === 0 ? 'y' : `y${i + 1}` })),
    ...eventTraces.map(t => ({ ...t, yaxis: 'y_events' })),
  ]

  const layout = {
    height:          totalH,
    paper_bgcolor:   'transparent',
    plot_bgcolor:    'transparent',
    showlegend:      false,
    margin:          { t: 10, b: 50, l: 90, r: 20 },
    xaxis: {
      title:     'Day since transplant',
      color:     '#9ca3af',
      gridcolor: '#2a2d3e',
      range:     [0, (totalDays || 400) + 5],
      tickfont:  { size: 10 },
    },
    font:    { color: '#9ca3af', size: 11 },
    shapes:  noteShapes,
    annotations: noteAnnotations,
    ...layoutYAxes,
  }

  // Fix yaxis → yaxis1 renaming for Plotly
  if (layout.yaxis1 && !layout.yaxis) {
    layout.yaxis = layout.yaxis1
    delete layout.yaxis1
  }

  return (
    <Plot
      data={allTraces}
      layout={layout}
      config={{ responsive: true, displayModeBar: true, scrollZoom: true }}
      style={{ width: '100%' }}
    />
  )
}
