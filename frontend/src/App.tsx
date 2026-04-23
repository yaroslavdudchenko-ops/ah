import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import ProtocolListPage from './pages/ProtocolListPage'
import CreateProtocolPage from './pages/CreateProtocolPage'
import ProtocolPage from './pages/ProtocolPage'
import AuditTrailPage from './pages/AuditTrailPage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/protocols" replace />} />
            <Route path="/protocols" element={<ProtocolListPage />} />
            <Route path="/protocols/new" element={<CreateProtocolPage />} />
            <Route path="/protocols/:id" element={<ProtocolPage />} />
            <Route path="/audit" element={<AuditTrailPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
