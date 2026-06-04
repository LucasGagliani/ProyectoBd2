import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getTrip, getTripStatus, updateTripStatus } from '../api/trips'
import { useAuth } from '../context/AuthContext'
import TripMap from '../components/TripMap'

const STATUS_LABELS = {
  pendiente: { label: 'Buscando conductor...', color: 'text-yellow-600 bg-yellow-50', dot: 'bg-yellow-400' },
  aceptado: { label: 'Conductor asignado', color: 'text-blue-600 bg-blue-50', dot: 'bg-blue-400' },
  en_curso: { label: 'Viaje en curso', color: 'text-green-600 bg-green-50', dot: 'bg-green-400' },
  finalizado: { label: 'Finalizado', color: 'text-gray-600 bg-gray-100', dot: 'bg-gray-400' },
  cancelado: { label: 'Cancelado', color: 'text-red-600 bg-red-50', dot: 'bg-red-400' },
}

const TRANSITIONS = {
  conductor: { pendiente: 'aceptado', aceptado: 'en_curso', en_curso: 'finalizado' },
  usuario: { pendiente: 'cancelado', aceptado: 'cancelado' },
}

const TRANSITION_LABELS = {
  aceptado: 'Aceptar viaje', en_curso: 'Iniciar viaje', finalizado: 'Finalizar viaje', cancelado: 'Cancelar viaje'
}

export default function TripDetail() {
  const { id } = useParams()
  const { role } = useAuth()
  const navigate = useNavigate()
  const [trip, setTrip] = useState(null)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState('')
  const [updating, setUpdating] = useState(false)
  const intervalRef = useRef(null)

  const fetchStatus = async () => {
    try {
      const { data } = await getTripStatus(id)
      setStatus(data.estado)
    } catch {}
  }

  useEffect(() => {
    getTrip(id).then(({ data }) => setTrip(data)).catch(() => setError('No se pudo cargar el viaje'))
    fetchStatus()
    intervalRef.current = setInterval(fetchStatus, 4000)
    return () => clearInterval(intervalRef.current)
  }, [id])

  const handleStatusUpdate = async (newStatus) => {
    setUpdating(true)
    try {
      await updateTripStatus(id, newStatus)
      setStatus(newStatus)
      if (newStatus === 'finalizado') navigate(`/trips/${id}/payment`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al actualizar estado')
    } finally {
      setUpdating(false)
    }
  }

  if (error) return <div className="max-w-lg mx-auto px-4 py-10 text-red-500">{error}</div>
  if (!trip) return <div className="max-w-lg mx-auto px-4 py-10 text-gray-400">Cargando...</div>

  const st = STATUS_LABELS[status] || STATUS_LABELS.pendiente
  const nextStatus = TRANSITIONS[role]?.[status]

  return (
    <div className="max-w-lg mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold mb-1">Viaje #{id}</h1>
      <p className="text-gray-500 text-sm mb-6">Detalle del viaje</p>

      <div className={`flex items-center gap-2 px-4 py-3 rounded-xl mb-6 ${st.color}`}>
        <span className={`w-2.5 h-2.5 rounded-full ${st.dot} animate-pulse`}></span>
        <span className="font-medium">{st.label}</span>
      </div>

      <TripMap
        origin={{ lat: trip.latitud_inicio, lon: trip.longitud_inicio }}
        destination={{ lat: trip.latitud_destino, lon: trip.longitud_destino }}
        className="mb-6"
      />

      <div className="bg-white border rounded-xl p-5 space-y-3 text-sm mb-6">
        <Row label="Origen" value={`${trip.latitud_inicio}, ${trip.longitud_inicio}`} />
        <Row label="Destino" value={`${trip.latitud_destino}, ${trip.longitud_destino}`} />
        {trip.distancia_km && <Row label="Distancia" value={`${trip.distancia_km} km`} />}
        {trip.tiempo_minutos && <Row label="Tiempo estimado" value={`${trip.tiempo_minutos} min`} />}
        {trip.id_conductor && <Row label="Conductor ID" value={trip.id_conductor} />}
        <Row label="Fecha" value={new Date(trip.fecha_hora).toLocaleString('es-AR')} />
      </div>

      {nextStatus && (
        <button onClick={() => handleStatusUpdate(nextStatus)} disabled={updating}
          className={`w-full py-3 rounded-xl font-medium disabled:opacity-50 ${nextStatus === 'cancelado' ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-black text-white hover:bg-gray-800'}`}>
          {updating ? 'Actualizando...' : TRANSITION_LABELS[nextStatus]}
        </button>
      )}

      {status === 'finalizado' && (
        <Link to={`/trips/${id}/payment`}
          className="block w-full text-center bg-black text-white py-3 rounded-xl font-medium hover:bg-gray-800 mt-3">
          Ver / Registrar pago
        </Link>
      )}
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-900">{value}</span>
    </div>
  )
}
