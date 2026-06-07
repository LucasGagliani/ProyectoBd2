import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Navbar from './components/Navbar'
import PrivateRoute from './components/PrivateRoute'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import NewTrip from './pages/NewTrip'
import TripDetail from './pages/TripDetail'
import DriverDashboard from './pages/DriverDashboard'
import Vehicles from './pages/Vehicles'
import Payment from './pages/Payment'
import Review from './pages/Review'
import TripHistory from './pages/TripHistory'

function AppRoutes() {
  const { isAuth, role } = useAuth()

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/login" element={!isAuth ? <Login /> : <Navigate to={role === 'conductor' ? '/driver' : '/dashboard'} replace />} />
        <Route path="/register" element={!isAuth ? <Register /> : <Navigate to={role === 'conductor' ? '/driver' : '/dashboard'} replace />} />

        <Route path="/dashboard" element={<PrivateRoute requiredRole="usuario"><Dashboard /></PrivateRoute>} />
        <Route path="/trips/new" element={<PrivateRoute requiredRole="usuario"><NewTrip /></PrivateRoute>} />
        <Route path="/trips/:id" element={<PrivateRoute><TripDetail /></PrivateRoute>} />
        <Route path="/trips/:id/payment" element={<PrivateRoute><Payment /></PrivateRoute>} />
        <Route path="/trips/:id/review" element={<PrivateRoute><Review /></PrivateRoute>} />
        <Route path="/trips/history" element={<PrivateRoute><TripHistory /></PrivateRoute>} />

        <Route path="/driver" element={<PrivateRoute requiredRole="conductor"><DriverDashboard /></PrivateRoute>} />
        <Route path="/driver/vehicles" element={<PrivateRoute requiredRole="conductor"><Vehicles /></PrivateRoute>} />

        <Route path="/" element={<Navigate to={isAuth ? (role === 'conductor' ? '/driver' : '/dashboard') : '/login'} replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
