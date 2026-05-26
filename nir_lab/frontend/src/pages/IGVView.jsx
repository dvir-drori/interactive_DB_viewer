/**
 * pages/IGVView.jsx
 * Secondary "Advanced" tab that embeds the original IGV-web viewer.
 * Points to the separate igv_static/ directory served as /igv-static/ by the backend.
 *
 * Intended for bioinformaticians who want to inspect raw bedGraph tracks.
 * Labeled clearly so non-technical users are not confused.
 */
export default function IGVView() {
  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      {/* Warning banner */}
      <div className="bg-purple-900/30 border-b border-purple-900/50 px-6 py-2 flex items-center gap-3 shrink-0">
        <span className="text-purple-300 font-medium text-sm">⬡ Advanced Genomic Viewer</span>
        <span className="text-gray-400 text-xs">
          This is the original IGV-web interface. Intended for bioinformatics use.
          For clinical overview, use the <a href="/patients" className="text-lab-accent hover:underline">Patients</a> page.
        </span>
      </div>

      {/* IGV iframe */}
      <iframe
        src="/igv-static/index.html"
        title="IGV Genomic Viewer"
        className="flex-1 w-full border-0"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
      />
    </div>
  )
}
