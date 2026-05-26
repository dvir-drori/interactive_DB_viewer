/**
 * components/NotesPanel.jsx
 * Right sidebar for adding, viewing, and deleting clinical notes per patient.
 * Notes are persisted in the database via the API.
 */
import { useState } from 'react'
import api from '../utils/api.js'

export default function NotesPanel({ patientId, notes, onNotesChange }) {
  const [newDay,     setNewDay]     = useState('')
  const [newContent, setNewContent] = useState('')
  const [saving,     setSaving]     = useState(false)
  const [error,      setError]      = useState(null)

  async function addNote() {
    if (!newContent.trim() || !newDay) return
    setSaving(true)
    setError(null)
    try {
      await api.post(`/patients/${patientId}/notes`, {
        day_offset: parseInt(newDay),
        content:    newContent.trim(),
      })
      setNewDay('')
      setNewContent('')
      onNotesChange()   // trigger refresh in parent
    } catch {
      setError('Failed to save note.')
    } finally {
      setSaving(false)
    }
  }

  async function deleteNote(id) {
    try {
      await api.delete(`/notes/${id}`)
      onNotesChange()
    } catch {
      setError('Failed to delete note.')
    }
  }

  return (
    <div className="w-60 shrink-0 bg-lab-panel border-l border-lab-border flex flex-col">
      <div className="p-3 border-b border-lab-border">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Clinical Notes
        </h2>

        {/* Add note form */}
        <input
          type="number"
          placeholder="Day offset (e.g. 30)"
          value={newDay}
          onChange={e => setNewDay(e.target.value)}
          className="w-full bg-lab-bg border border-lab-border rounded px-2 py-1 text-xs mb-2 focus:outline-none focus:border-lab-accent"
        />
        <textarea
          placeholder="Add a clinical note…"
          value={newContent}
          onChange={e => setNewContent(e.target.value)}
          rows={3}
          className="w-full bg-lab-bg border border-lab-border rounded px-2 py-1 text-xs mb-2 resize-none focus:outline-none focus:border-lab-accent"
        />
        {error && <p className="text-xs text-red-400 mb-1">{error}</p>}
        <button
          onClick={addNote}
          disabled={saving || !newContent.trim() || !newDay}
          className="w-full bg-lab-accent text-white text-xs py-1.5 rounded hover:bg-blue-600 disabled:opacity-40 transition-colors"
        >
          {saving ? 'Saving…' : 'Add Note'}
        </button>
      </div>

      {/* Notes list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {(!notes || notes.length === 0) && (
          <p className="text-xs text-gray-500 text-center mt-4">No notes yet.</p>
        )}
        {(notes || []).map(note => (
          <div key={note.id} className="bg-lab-bg border border-lab-border rounded p-2">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-mono text-lab-accent">Day {note.day_offset}</span>
              <button
                onClick={() => deleteNote(note.id)}
                className="text-xs text-gray-600 hover:text-red-400 transition-colors"
                title="Delete note"
              >
                ✕
              </button>
            </div>
            {note.date && (
              <p className="text-xs text-gray-500 mb-1">{note.date}</p>
            )}
            <p className="text-xs text-gray-300 whitespace-pre-wrap">{note.content}</p>
            <p className="text-xs text-gray-600 mt-1">
              {new Date(note.created_at).toLocaleDateString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
