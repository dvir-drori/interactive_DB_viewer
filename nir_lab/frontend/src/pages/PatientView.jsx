/**
 * pages/PatientView.jsx
 * Single-patient drill-down view.
 *
 * Layout:
 *   [TrackSelector sidebar] | [Charts area] | [NotesPanel sidebar]
 *
 * Charts area contains:
 *   - TimelineChart  (Lab Data lines + Clinical Events)
 *   - ChipSeqTrack   (heatmap for H3K4me3 and other ChIP-seq markers)
 */
import { useState, useEffect, useCallback } from 'react'
import { useParams, Link }                  from 'react-router-dom'
import api             from '../utils/api.js'
import TrackSelector   from '../components/TrackSelector.jsx'
import TimelineChart   from '../components/TimelineChart.jsx'
import ChipSeqTrack    from '../components/ChipSeqTrack.jsx'
import NotesPanel      from '../components/NotesPanel.jsx'

const CHIPSEQ_LABELS = ['H3K4me3', 'H3K27ac', 'H3K27me3', 'H3K9me3']

export default function PatientView() {
  const { id } = useParams()

  const [summary,        setSummary]        = useState(null)
  const [measurements,   setMeasurements]   = useState([])
  const [events,         setEvents]         = useState([])
  const [notes,          setNotes]          = useState([])
  const [activeLabels,   setActiveLabels]   = useState(new Set())
  const [loading,        setLoading]        = useState(true)
  const [error,          setError]          = useState(null)

  // Load patient summary + events + notes on mount
  useEffect(() => {
    if (!id) return
    setLoading(true)
    Promise.all([
      api.get(`/patients/${id}/summary`),
      api.get(`/patients/${id}/events`),
      api.get(`/patients/${id}/notes`),
    ])
      .then(([sumRes, evtRes, notesRes]) => {
        setSummary(sumRes.data)
        setEvents(evtRes.data)
        setNotes(notesRes.data)

        // Default: activate all Lab Data labels
        const labLabels = sumRes.data.labels_by_category?.['Lab Data'] || []
        setActiveLabels(new Set(labLabels))
      })
      .catch(() => setError('Failed to load patient data.'))
      .finally(() => setLoading(false))
  }, [id])

  // Reload measurements whenever activeLabels changes
  useEffect(() => {
    if (activeLabels.size === 0) {
      setMeasurements([])
      return
    }
    const labelsParam = [...activeLabels].join(',')
    api.get(`/patients/${id}/measurements`, { params: { labels: labelsParam } })
      .then(r => setMeasurements(r.data))
      .catch(() => {})
  }, [id, activeLabels])

  const refreshNotes = useCallback(() => {
    api.get(`/patients/${id}/notes`).then(r => setNotes(r.data))
  }, [id])

  if (loading) return <div className="p-8 text-gray-400">Loading…</div>
  if (error)   return <div className="p-8 text-red-400">{error}</div>
  if (!summary) return null

  // Separate lab data from ChIP-seq within measurements
  const labMeasurements  = measurements.filter(m => m.category === 'Lab Data')
  const chipMeasurements = measurements.filter(m => CHIPSEQ_LABELS.includes(m.label))

  return (
    <div className="flex h-[calc(100vh-3rem)] overflow-hidden">
      {/* ── Left: Track Selector ── */}
      <TrackSelector
        labelsByCategory={summary.labels_by_category}
        activeLabels={activeLabels}
        onChange={setActiveLabels}
      />

      {/* ── Centre: Charts ── */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Breadcrumb */}
        <div className="flex items-baseline gap-2 mb-4">
          <Link to="/patients" className="text-xs text-gray-500 hover:text-gray-300">
            ← All patients
          </Link>
          <h1 className="text-xl font-semibold font-mono text-lab-accent">{id}</h1>
          <span className="text-sm text-gray-400">
            {summary.first_date} → {summary.last_date}
            &nbsp;·&nbsp;{summary.total_days} days
          </span>
        </div>

        {/* Lab Data + Events chart */}
        {(labMeasurements.length > 0 || events.length > 0) ? (
          <div className="bg-lab-panel rounded-lg border border-lab-border p-3 mb-4">
            <TimelineChart
              labData={labMeasurements}
              events={events}
              notes={notes}
              totalDays={summary.total_days}
              firstDate={summary.first_date}
            />
          </div>
        ) : (
          <div className="bg-lab-panel rounded-lg border border-lab-border p-8 text-center text-gray-500 mb-4">
            Select tracks on the left to display data.
          </div>
        )}

        {/* ChIP-seq heatmap */}
        {chipMeasurements.length > 0 && (
          <div className="bg-lab-panel rounded-lg border border-purple-900/40 p-3">
            <ChipSeqTrack
              measurements={chipMeasurements}
              patientId={id}
              totalDays={summary.total_days}
            />
          </div>
        )}
      </div>

      {/* ── Right: Notes Panel ── */}
      <NotesPanel
        patientId={id}
        notes={notes}
        onNotesChange={refreshNotes}
      />
    </div>
  )
}
