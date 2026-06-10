import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getTripHistory } from '../api/trips'

const ESTADO_COLORS = {
  finalizado: 'text-green-600 bg-green-50',
  cancelado: 'text-red-600 bg-red-50',
}

const PAGO_COLORS = {
  aprobado: 'text-green-600',
  pendiente: 'text-yellow-600',
  rechazado: 'text-red-600',
  reembolsado: 'text-gray-600',
}

function getReviewSummary(trip) {
  if (trip.resenas_completas) {
    return { label: 'Resenas: completas', className: 'text-green-600' }
  }
  if (trip.mi_resena) {
    return { label: 'Resenas: parcial', className: 'text-blue-600' }
  }
  return { label: 'Resenas: pendiente', className: 'text-gray-500' }
}

export default function TripHistory() {
  const { role } = useAuth()
  const [trips, setTrips] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getTripHistory()
      .then(({ data }) => setTrips(data))
      .catch(() => setError('Error al cargar el historial'))
      .finally(() => setLoading(false))
  }, [])

  const backPath = role === 'conductor' ? '/driver' : '/dashboard'

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Historial de viajes</h1>
          <p className="text-gray-500 text-sm">Viajes finalizados y cancelados</p>
        </div>
        <Link to={backPath} className="text-sm text-gray-500 hover:text-black">
          Volver
        </Link>
      </div>

      {loading && <p className="text-gray-400 text-center py-8">Cargando...</p>}
      {error && <p className="text-red-500 text-center py-8">{error}</p>}

      {!loading && !error && trips.length === 0 && (
        <p className="text-gray-400 text-center py-8">No tenes viajes en el historial</p>
      )}

      <div className="space-y-3">
        {trips.map((trip) => {
          const reviewSummary = getReviewSummary(trip)

          return (
            <div key={trip.id_viaje} className="bg-white border rounded-xl p-4">
              <div className="flex justify-between items-start mb-2">
                <span className="font-medium text-sm">Viaje #{trip.id_viaje}</span>
                <span className={`text-xs px-2 py-1 rounded-full capitalize ${ESTADO_COLORS[trip.estado] || ''}`}>
                  {trip.estado}
                </span>
              </div>

              <p className="text-xs text-gray-500">
                {trip.fecha_hora ? new Date(trip.fecha_hora).toLocaleString('es-AR') : ''}
              </p>
              {trip.distancia_km && (
                <p className="text-xs text-gray-400 mt-1">{trip.distancia_km} km</p>
              )}

              <div className="flex flex-wrap gap-3 mt-3 text-xs">
                {trip.monto_total != null && (
                  <span className="text-gray-600">Total: <strong>${trip.monto_total}</strong></span>
                )}
                {trip.estado_pago && (
                  <span className={PAGO_COLORS[trip.estado_pago] || 'text-gray-500'}>
                    Pago: {trip.estado_pago}
                  </span>
                )}
                {trip.estado === 'finalizado' && !trip.estado_pago && role === 'usuario' && (
                  <Link
                    to={`/trips/${trip.id_viaje}/payment`}
                    className="text-amber-700 font-medium hover:underline"
                  >
                    Pagar viaje
                  </Link>
                )}
                {trip.estado === 'finalizado' && trip.estado_pago === 'aprobado' && !trip.mi_resena && (
                  <Link
                    to={`/trips/${trip.id_viaje}/review`}
                    className="text-blue-600 font-medium hover:underline"
                  >
                    {role === 'conductor' ? 'Calificar pasajero' : 'Dejar resena'}
                  </Link>
                )}
                {trip.mi_resena && (
                  <span className="text-green-600">Resena enviada</span>
                )}
                {trip.estado === 'finalizado' && trip.estado_pago === 'aprobado' && (
                  <span className={reviewSummary.className}>{reviewSummary.label}</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
