import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { registerUsuario, registerConductor, loginUser } from '../api/auth'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [role, setRole] = useState('usuario')
  const [form, setForm] = useState({ nombre: '', email: '', telefono: '', contrasena: '', nro_licencia: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = { nombre: form.nombre, email: form.email, contrasena: form.contrasena }
      if (form.telefono) payload.telefono = form.telefono
      if (role === 'conductor') payload.nro_licencia = form.nro_licencia

      role === 'conductor' ? await registerConductor(payload) : await registerUsuario(payload)

      const { data } = await loginUser(form.email, form.contrasena)
      login(data.access_token, data.role, data.user_id)
      navigate(data.role === 'conductor' ? '/driver' : '/dashboard')
    } catch (err) {
      // Manejar diferentes tipos de errores
      let errorMsg = 'Error al registrarse'
      if (err.response?.data) {
        const detail = err.response.data.detail
        if (typeof detail === 'string') {
          errorMsg = detail
        } else if (Array.isArray(detail)) {
          // Error de validación de Pydantic
          errorMsg = detail.map(e => `${e.loc?.[1] || 'campo'}: ${e.msg}`).join('; ')
        } else if (detail?.msg) {
          errorMsg = detail.msg
        }
      }
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const field = (label, key, type = 'text', placeholder = '') => (
    <div>
      <label className="block text-sm font-medium mb-1">{label}</label>
      <input
        type={type} value={form[key]} placeholder={placeholder}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black"
        required={key !== 'telefono'}
      />
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-10">
      <div className="bg-white rounded-2xl shadow-md w-full max-w-md p-8">
        <h1 className="text-2xl font-bold mb-1">Crear cuenta</h1>
        <p className="text-gray-500 text-sm mb-6">Registrate en UberTPO</p>

        <div className="flex rounded-lg overflow-hidden border mb-6">
          {['usuario', 'conductor'].map((r) => (
            <button key={r} onClick={() => setRole(r)}
              className={`flex-1 py-2 text-sm font-medium capitalize transition ${role === r ? 'bg-black text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}>
              {r === 'usuario' ? 'Pasajero' : 'Conductor'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {field('Nombre completo', 'nombre', 'text', 'Juan Pérez')}
          {field('Email', 'email', 'email', 'tu@email.com')}
          {field('Teléfono (opcional)', 'telefono', 'tel', '+54 11 1234-5678')}
          {field('Contraseña', 'contrasena', 'password', '••••••')}
          {role === 'conductor' && field('Número de licencia', 'nro_licencia', 'text', 'ABC123456')}

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button type="submit" disabled={loading}
            className="w-full bg-black text-white py-2 rounded-lg font-medium hover:bg-gray-800 disabled:opacity-50">
            {loading ? 'Registrando...' : 'Crear cuenta'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          ¿Ya tenés cuenta?{' '}
          <Link to="/login" className="text-black font-medium hover:underline">Iniciá sesión</Link>
        </p>
      </div>
    </div>
  )
}
