import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMe } from '../api/users'

export default function Dashboard() {
  const [user, setUser] = useState(null)

  useEffect(() => {
    getMe().then(({ data }) => setUser(data)).catch(() => {})
  }, [])

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold mb-1">
        Hola{user ? `, ${user.nombre.split(' ')[0]}` : ''} 👋
      </h1>
      <p className="text-gray-500 text-sm mb-8">¿A dónde querés ir hoy?</p>

      <Link to="/trips/new"
        className="block w-full bg-black text-white text-center py-4 rounded-xl text-lg font-medium hover:bg-gray-800 mb-6">
        Pedir un viaje
      </Link>

      {user && (
        <div className="bg-white border rounded-xl p-5">
          <h2 className="font-semibold mb-3 text-gray-700">Tu perfil</h2>
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex justify-between"><span>Nombre</span><span className="font-medium text-gray-900">{user.nombre}</span></div>
            <div className="flex justify-between"><span>Email</span><span className="font-medium text-gray-900">{user.email}</span></div>
            {user.telefono && <div className="flex justify-between"><span>Teléfono</span><span className="font-medium text-gray-900">{user.telefono}</span></div>}
            <div className="flex justify-between"><span>Calificación</span><span className="font-medium text-gray-900">⭐ {user.calificacion_promedio}</span></div>
          </div>
        </div>
      )}
    </div>
  )
}
