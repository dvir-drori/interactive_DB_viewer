/**
 * pages/CompareView.jsx
 * Multi-patient comparison view.
 *
 * Reads ?patients=P001,P002,... from the URL query string.
 * Lets the user choose a label to compare, then shows all patients
 * as overlaid lines on a single chart aligned to Day 1.
 *
 * ChIP-seq tracks are shown as stacked heatmap rows (one per patient).
 */
import { useState, useEffect }  from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import Plot                      from 'react-plotly.js'
import api                       from '../utils/api.js'

const PALETTE = ['#4f8ef7','#f59e0b','#10b981','#ef4444','#8b5cf6','#06b6d4']
const CHIPSEQ_LABELS = ['H3K4me3', 'H3K27ac', 'H3K27me3', 'H3K9me3']

export default function CompareView() {
  const [searchParams]           = useSearchParams()
  const patientIds                = (searchParams.get('patients') || '').split(',').filter(Boolean)

  const [allLabels,   setAllLabels]   = useState([])
  const [activeLabel, setActiveLabel] = useState('')
  const [compareData, setCompareData] = useState({})
  const [hidden,      setHidden]      = useState(new Set())
  const [loading,     setLoading]     = useState(false)

  // Fetch available labels for the first patient to populate the dropdown
  useEffect(() => {
    if (patientIds.length === 0) return
    api.get(`/patients/${patientIds[0]}/summary`).then(r => {
      const labLabels = r.data.labels_by_category?.['Lab Data'] || []
      setAllLabels(labLabels)
      if (labLabels.length > 0) setActiveLabel(labLabels[0])
    })
  }, [patientIds.join(',')])

  // Fetch comparison data when label changes
  useEffect(() => {
    if (!activeLabel || patientIds.length === 0) return
    setLoading(true)
    api.get('/compare', {
      params: { patients: patientIds.join(','), label: activeLabel },
    })
      .then(r => setCompareData(r.data))
      .finally(() => setLoading(false))
  }, [activeLabel, patientIds.join(',')])

  function togglePatient(pid) {
    setHidden(prev => {
      const next = new Set(prev)
      next.has(pid) ? next.delete(pid) : next.add(pid)
      return next
    })
  }

  if (patientIds.length === 0) {
    return (
      <div className="p-8 text-gray-400">
        No patients selected. <Link to="/patients" className="text-lab-accent hover:underline">Go back to patient list</Link> and select 2+ patients.
      </div>
    )
  }

  // Build Plotly traces
  const traces = patientIds.map((pid, i) => {
    const pts = compareData[pid] || []
    return {
      type:    'scatter',
      mode:    'lines+markers',
      name:    pid,
      x:       pts.map(p => p.day_offset),
      y:       pts.map(p => parseFloat(p.value)),
      line:    { color: PALETTE[i % PALETTE.length], width: 2 },
      marker:  { size: 5 },
      visible: hidden.has(pid) ? 'legendonly' : true,
      hovertemplate: `<b>${pid}</b><br>Day %{x}<br>${activeLabel}: %{y}<extra></extra>`,
    }
  })

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-baseline gap-3 mb-6">
        <Link to="/patients" className="text-xs text-gray-500 hover:text-gray-300">← Patients</Link>
        <h1 className="text-2xl font-semibold">Compare Patients</h1>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-4 mb-6 items-center">
        {/* Label selector */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Label:</label>
          <select
            value={activeLabel}
            onChange={e => setActiveLabel(e.target.value)}
            className="bg-lab-panel border border-lab-border rounded px-3 py-1.5 text-sm focus:outline-none focus:border-lab-accent"
          >
            {allLabels.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>

        {/* Patient toggles */}
        <div className="flex flex-wrap gap-2">
          {patientIds.map((pid, i) => (
            <button
              key={pid}
              onClick={() => togglePatient(pid)}
              className={`text-xs px-3 py-1 rounded border transition-colors ${
                hidden.has(pid)
                  ? 'border-lab-border text-gray-500'
                  : 'border-transparent text-white'
              }`}
              style={hidden.has(pid) ? {} : { backgroundColor: PALETTE[i % PALETTE.length] + '33', borderColor: PALETTE[i % PALETTE.length] }}
            >
              {pid}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="bg-lab-panel rounded-lg border border-lab-border p-4 mb-6">
        {loading ? (
          <div className="h-64 flex items-center justify-center text-gray-500">Loading…</div>
        ) : (
          <Plot
            data={traces}
            layout={{
              height:        400,
              paper_bgcolor: 'transparent',
              plot_bgcolor:  'transparent',
              margin:        { t: 20, b: 50, l: 70, r: 20 },
              xaxis: {
                title:     'Day since transplant (Day 1 = transplant date)',
                color:     '#9ca3af',
                gridcolor: '#2a2d3e',
                tickfont:  { size: 10 },
              },
              yaxis: {
                title:     activeLabel,
                color:     '#9ca3af',
                gridcolor: '#2a2d3e',
                zeroline:  false,
                tickfont:  { size: 10 },
              },
              legend: {
                font:      { color: '#9ca3af', size: 11 },
                bgcolor:   'transparent',
                bordercolor: '#2a2d3e',
              },
              font: { color: '#9ca3af', size: 11 },
            }}
            config={{ responsive: true, displayModeBar: true, scrollZoom: true }}
            style={{ width: '100%' }}
          />
        )}
      </div>

      {/* Note about ChIP-seq */}
      {CHIPSEQ_LABELS.includes(activeLabel) && (
        <div className="bg-purple-900/20 border border-purple-900/40 rounded p-3 text-sm text-purple-300">
          ChIP-seq label selected. Values represent enrichment levels: 1 = Low, 2 = Moderate, 3 = High.
        </div>
      )}
    </div>
  )
}
