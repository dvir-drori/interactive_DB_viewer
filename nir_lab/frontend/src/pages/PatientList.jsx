/**
 * pages/PatientList.jsx
 * Overview table of all patients.
 * Allows searching by ID and selecting patients for comparison.
 */
import { useState, useEffect } from 'react'
import { useNavigate }          from 'react-router-dom'
import api                      from '../utils/api.js'

export default function PatientList() {
  const [patients,  setPatients]  = useState([])
  const [search,    setSearch]    = useState('')
  const [selected,  setSelected]  = useState([])   // patient IDs checked for comparison
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/patients')
      .then(r => setPatients(r.data))
      .catch(() => setError('Could not load patients. Is the backend running?'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = patients.filter(p =>
    p.id.toLowerCase().includes(search.toLowerCase())
  )

  function toggleSelect(id) {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  function goCompare() {
    navigate(`/compare?patients=${selected.join(',')}`)
  }

  if (loading) return <div className="p-8 text-gray-400">Loading patients…</div>
  if (error)   return <div className="p-8 text-red-400">{error}</div>

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-semibold mb-6">Patient Overview</h1>

      {/* Search + Compare button */}
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="Search patient ID…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="bg-lab-panel border border-lab-border rounded px-3 py-1.5 text-sm w-64 focus:outline-none focus:border-lab-accent"
        />
        {selected.length >= 2 && (
          <button
            onClick={goCompare}
            className="bg-lab-accent text-white text-sm px-4 py-1.5 rounded hover:bg-blue-600 transition-colors"
          >
            Compare {selected.length} patients
          </button>
        )}
      </div>

      {/* Table */}
      <div className="bg-lab-panel rounded-lg border border-lab-border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-lab-border text-gray-400 text-xs uppercase tracking-wider">
              <th className="px-4 py-3 text-left w-8"></th>
              <th className="px-4 py-3 text-left">Patient ID</th>
              <th className="px-4 py-3 text-left">First Date</th>
              <th className="px-4 py-3 text-left">Last Date</th>
              <th className="px-4 py-3 text-right">Follow-up (days)</th>
              <th className="px-4 py-3 text-right">Measurements</th>
              <th className="px-4 py-3 text-left"></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p, i) => (
              <tr
                key={p.id}
                className={`border-b border-lab-border hover:bg-lab-border/30 transition-colors cursor-pointer ${i % 2 === 0 ? '' : 'bg-white/[0.02]'}`}
              >
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selected.includes(p.id)}
                    onChange={() => toggleSelect(p.id)}
                    onClick={e => e.stopPropagation()}
                    className="accent-lab-accent"
                  />
                </td>
                <td className="px-4 py-3 font-mono text-lab-accent font-medium"
                    onClick={() => navigate(`/patients/${p.id}`)}>
                  {p.id}
                </td>
                <td className="px-4 py-3 text-gray-300"
                    onClick={() => navigate(`/patients/${p.id}`)}>
                  {p.first_date}
                </td>
                <td className="px-4 py-3 text-gray-300"
                    onClick={() => navigate(`/patients/${p.id}`)}>
                  {p.last_date}
                </td>
                <td className="px-4 py-3 text-right text-gray-300"
                    onClick={() => navigate(`/patients/${p.id}`)}>
                  {p.total_days}
                </td>
                <td className="px-4 py-3 text-right text-gray-300"
                    onClick={() => navigate(`/patients/${p.id}`)}>
                  {p.measurement_count}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => navigate(`/patients/${p.id}`)}
                    className="text-xs text-lab-accent hover:underline"
                  >
                    View →
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                  {patients.length === 0
                    ? 'No patients found. Upload a CSV file to get started.'
                    : 'No patients match your search.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="mt-3 text-xs text-gray-500">
        {patients.length} patients total · Select 2+ to compare
      </p>
    </div>
  )
}
