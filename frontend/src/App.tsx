import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ProtocolListPage from './pages/ProtocolListPage'
import CreateProtocolPage from './pages/CreateProtocolPage'
import ProtocolPage from './pages/ProtocolPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/protocols" replace />} />
          <Route path="/protocols" element={<ProtocolListPage />} />
          <Route path="/protocols/new" element={<CreateProtocolPage />} />
          <Route path="/protocols/:id" element={<ProtocolPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
