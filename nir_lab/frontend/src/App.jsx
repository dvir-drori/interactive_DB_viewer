/**
 * App.jsx
 * Root component — sets up React Router and the top-level layout:
 *   - Fixed top navigation bar
 *   - Route definitions for all pages
 */
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import PatientList  from './pages/PatientList.jsx'
import PatientView  from './pages/PatientView.jsx'
import CompareView  from './pages/CompareView.jsx'
import UploadPage   from './pages/UploadPage.jsx'
import IGVView      from './pages/IGVView.jsx'

function NavItem({ to, label }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `px-4 py-2 rounded text-sm font-medium transition-colors ${
          isActive
            ? 'bg-lab-accent text-white'
            : 'text-gray-400 hover:text-white hover:bg-lab-border'
        }`
      }
    >
      {label}
    </NavLink>
  )
}

export default function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/+$/, '')}>
      {/* ── Top navigation bar ── */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-lab-panel border-b border-lab-border h-12 flex items-center px-6 gap-6">
        <span className="text-lab-accent font-semibold text-sm tracking-wide mr-4">
          NIR Lab · Transplant Timeline
        </span>
        <NavItem to="/patients" label="Patients" />
        <NavItem to="/compare"  label="Compare"  />
        <NavItem to="/upload"   label="Upload"   />
        <NavItem to="/igv"      label="IGV (Advanced)" />
      </header>

      {/* ── Page content (offset for fixed nav) ── */}
      <main className="pt-12 min-h-screen bg-lab-bg">
        <Routes>
          <Route path="/"                   element={<PatientList />} />
          <Route path="/patients"           element={<PatientList />} />
          <Route path="/patients/:id"       element={<PatientView />} />
          <Route path="/compare"            element={<CompareView />} />
          <Route path="/upload"             element={<UploadPage />}  />
          <Route path="/igv"                element={<IGVView />}     />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
