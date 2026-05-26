/**
 * pages/UploadPage.jsx
 * CSV upload interface with drag-and-drop, preview, and upload history.
 */
import { useState, useEffect, useRef } from 'react'
import api from '../utils/api.js'

export default function UploadPage() {
  const [file,        setFile]        = useState(null)
  const [preview,     setPreview]     = useState(null)   // first 5 rows of CSV
  const [uploading,   setUploading]   = useState(false)
  const [result,      setResult]      = useState(null)
  const [history,     setHistory]     = useState([])
  const [dragOver,    setDragOver]    = useState(false)
  const inputRef = useRef()

  useEffect(() => { loadHistory() }, [])

  function loadHistory() {
    api.get('/upload/history').then(r => setHistory(r.data)).catch(() => {})
  }

  function handleFile(f) {
    if (!f || !f.name.endsWith('.csv')) {
      alert('Please select a .csv file.')
      return
    }
    setFile(f)
    setResult(null)

    // Build a quick text preview
    const reader = new FileReader()
    reader.onload = e => {
      const lines = e.target.result.split('\n').slice(0, 6)
      setPreview(lines)
    }
    reader.readAsText(f)
  }

  async function uploadFile() {
    if (!file) return
    setUploading(true)
    setResult(null)
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult({ success: true, ...res.data })
      setFile(null)
      setPreview(null)
      loadHistory()
    } catch (err) {
      const detail = err.response?.data?.detail
      setResult({ success: false, errors: Array.isArray(detail) ? detail : [String(detail)] })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-8">
      <h1 className="text-2xl font-semibold">Upload Patient Data</h1>

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]) }}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          dragOver ? 'border-lab-accent bg-lab-accent/10' : 'border-lab-border hover:border-gray-500'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={e => handleFile(e.target.files[0])}
        />
        <div className="text-4xl mb-3">📂</div>
        <p className="text-gray-300 font-medium">
          {file ? file.name : 'Drag & drop a CSV file here, or click to browse'}
        </p>
        <p className="text-xs text-gray-500 mt-2">
          Required columns: PatientID · Date · Label · Value · Category
        </p>
      </div>

      {/* Preview */}
      {preview && (
        <div>
          <p className="text-xs text-gray-400 mb-2 uppercase tracking-wider">File preview (first 5 rows)</p>
          <div className="bg-lab-panel border border-lab-border rounded overflow-x-auto">
            <table className="text-xs w-full">
              <tbody>
                {preview.map((line, i) => (
                  <tr key={i} className={i === 0 ? 'bg-lab-border/30 font-medium' : ''}>
                    {line.split(',').map((cell, j) => (
                      <td key={j} className="px-3 py-1.5 border-b border-lab-border/50 font-mono truncate max-w-xs">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Upload button */}
      {file && (
        <button
          onClick={uploadFile}
          disabled={uploading}
          className="bg-lab-accent text-white px-6 py-2 rounded hover:bg-blue-600 disabled:opacity-50 transition-colors"
        >
          {uploading ? 'Uploading…' : `Upload ${file.name}`}
        </button>
      )}

      {/* Result */}
      {result && (
        <div className={`rounded-lg border p-4 ${
          result.success ? 'border-green-700 bg-green-900/20' : 'border-red-700 bg-red-900/20'
        }`}>
          {result.success ? (
            <>
              <p className="text-green-400 font-medium mb-1">✓ Upload successful</p>
              <p className="text-sm text-gray-300">
                {result.patient_count} patients · {result.row_count} measurements ingested
              </p>
              {result.errors?.length > 0 && (
                <ul className="mt-2 text-xs text-yellow-400 space-y-0.5">
                  {result.errors.map((e, i) => <li key={i}>⚠ {e}</li>)}
                </ul>
              )}
            </>
          ) : (
            <>
              <p className="text-red-400 font-medium mb-1">✗ Upload failed</p>
              <ul className="text-xs text-red-300 space-y-0.5">
                {result.errors?.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </>
          )}
        </div>
      )}

      {/* Upload history */}
      {history.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Upload History
          </h2>
          <div className="bg-lab-panel rounded-lg border border-lab-border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-lab-border text-xs text-gray-500 uppercase">
                  <th className="px-4 py-2 text-left">Filename</th>
                  <th className="px-4 py-2 text-left">Date</th>
                  <th className="px-4 py-2 text-right">Patients</th>
                  <th className="px-4 py-2 text-right">Rows</th>
                  <th className="px-4 py-2 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {history.map(u => (
                  <tr key={u.id} className="border-b border-lab-border/50">
                    <td className="px-4 py-2 font-mono text-xs text-gray-300">{u.filename}</td>
                    <td className="px-4 py-2 text-xs text-gray-400">
                      {new Date(u.uploaded_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-right text-xs text-gray-300">{u.patient_count ?? '—'}</td>
                    <td className="px-4 py-2 text-right text-xs text-gray-300">{u.row_count ?? '—'}</td>
                    <td className="px-4 py-2 text-xs">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        u.status === 'ok'      ? 'bg-green-900/40 text-green-400' :
                        u.status === 'partial' ? 'bg-yellow-900/40 text-yellow-400' :
                                                  'bg-red-900/40 text-red-400'
                      }`}>
                        {u.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
