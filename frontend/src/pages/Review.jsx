import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getTripReviewStatus, createReview } from '../api/reviews'

export default function Review() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { role } = useAuth()

  const [status, setStatus] = useState(null)
  const [calificacion, setCalificacion] = useState(5)
  const [comentario, setComentario] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getTripReviewStatus(id)
      .then(({ data }) => setStatus(data))
      .catch(() => setError('No se pudo cargar el estado de reseñas'))
  }, [id])

  const handleSubmit = async () => {
    setLoading(true)
    setError('')
    try {
      await createReview({
        id_viaje: parseInt(id),
        calificacion,
        comentario: comentario || null,
      })
      navigate('/trips/history')
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al enviar la reseña')
    } finally {
      setLoading(false)
    }
  }

  const targetLabel = role === 'conductor' ? 'al pasajero' : 'al conductor'

  if (!status) {
    return (
      <div className="max-w-lg mx-auto px-4 py-10 text-gray-400">
        {error || 'Cargando...'}
      </div>
    )
  }

  if (status.mi_resena) {
    return (
      <div className="max-w-lg mx-auto px-4 py-10 text-center">
        <p className="text-green-700 font-medium mb-4">Ya dejaste tu reseña para este viaje</p>
        <button
          onClick={() => navigate('/trips/history')}
          className="bg-black text-white px-6 py-2 rounded-xl text-sm"
        >
          Ver historial
        </button>
      </div>
    )
  }

  if (!status.puede_resenar) {
    return (
      <div className="max-w-lg mx-auto px-4 py-10 text-center">
        <p className="text-gray-600 mb-2">Todavía no podés dejar una reseña</p>
        <p className="text-sm text-gray-400 mb-4">
          El viaje debe estar finalizado y el pago aprobado
        </p>
        <button
          onClick={() => navigate(role === 'conductor' ? '/driver' : '/dashboard')}
          className="bg-black text-white px-6 py-2 rounded-xl text-sm"
        >
          Volver
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold mb-1">Reseña — Viaje #{id}</h1>
      <p className="text-gray-500 text-sm mb-8">
        Calificá tu experiencia {targetLabel}
      </p>

      <div className="bg-white border rounded-xl p-5 space-y-5">
        <div>
          <label className="block font-medium mb-3">Calificación</label>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map(n => (
              <button
                key={n}
                type="button"
                onClick={() => setCalificacion(n)}
                className={`w-10 h-10 rounded-full text-lg transition ${
                  calificacion >= n ? 'text-yellow-500' : 'text-gray-300'
                }`}
              >
                ★
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-1">{calificacion} de 5 estrellas</p>
        </div>

        <div>
          <label className="block font-medium mb-2">Comentario (opcional)</label>
          <textarea
            value={comentario}
            onChange={e => setComentario(e.target.value)}
            rows={4}
            placeholder="Contanos cómo fue el viaje..."
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black resize-none"
          />
        </div>
      </div>

      {error && <p className="text-red-500 text-sm mt-4">{error}</p>}

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full mt-6 bg-black text-white py-3 rounded-xl font-medium hover:bg-gray-800 disabled:opacity-50"
      >
        {loading ? 'Enviando...' : 'Enviar reseña'}
      </button>
    </div>
  )
}
