import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/useAuthStore'
import AuthView from './views/AuthView'
import MainView from './views/MainView'

const ProtectedRoute = ({ children }) => {
  const { token } = useAuthStore()
  if (!token) {
    return <Navigate to="/auth" replace />
  }
  return children
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/auth" element={<AuthView />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainView />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App