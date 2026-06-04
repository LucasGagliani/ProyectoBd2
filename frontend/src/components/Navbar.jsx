import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { isAuth, role, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <nav className="bg-black text-white px-6 py-3 flex items-center justify-between shadow">
      <Link to="/" className="text-xl font-bold tracking-tight">UberTPO</Link>
      {isAuth && (
        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-400 capitalize">{role}</span>
          {role === 'usuario' && (
            <>
              <Link to="/dashboard" className="hover:text-gray-300">Inicio</Link>
              <Link to="/trips/new" className="hover:text-gray-300">Pedir viaje</Link>
            </>
          )}
          {role === 'conductor' && (
            <>
              <Link to="/driver" className="hover:text-gray-300">Panel</Link>
              <Link to="/driver/vehicles" className="hover:text-gray-300">Vehículos</Link>
            </>
          )}
          <button onClick={handleLogout} className="bg-white text-black px-3 py-1 rounded hover:bg-gray-200 font-medium">
            Salir
          </button>
        </div>
      )}
    </nav>
  )
}
