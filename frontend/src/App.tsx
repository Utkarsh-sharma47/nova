import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { DashboardPage } from './pages/DashboardPage'
import { DocumentPage } from './pages/DocumentPage'
import { QueryPage } from './pages/QueryPage'
import { ShipmentPage } from './pages/ShipmentPage'
import { UploadPage } from './pages/UploadPage'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="documents/:documentId" element={<DocumentPage />} />
          <Route path="shipments/:shipmentId" element={<ShipmentPage />} />
          <Route path="query" element={<QueryPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
