import { useEffect, useState, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getDriverMe, updateDriverStatus, updateDriverLocation } from '../api/drivers'
import { getMyTrips, getTripHistory } from '../api/trips'
import TripMap from '../components/TripMap'

const ESTADOS = ['disponible', 'ocupado', 'inactivo']
const ESTADO_COLORS = {
  disponible: 'bg-green-100 text-green-700 border-green-200',
  ocupado: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  inactivo: 'bg-gray-100 text-gray-500 border-gray-200',
}
const STATUS_LABELS = {
  pendiente: { label: 'Pendiente', color: 'text-yellow-600 bg-yellow-50' },
  aceptado: { label: 'Aceptado', color: 'text-blue-600 bg-blue-50' },
  en_curso: { label: 'En curso', color: 'text-green-600 bg-green-50' },
}

const BARRIOS = {
  Palermo: [-34.5885, -58.4344],
  Belgrano: [-34.5587, -58.4580],
  'San Telmo': [-34.6211, -58.3731],
  Recoleta: [-34.5877, -58.3927],
  Flores: [-34.6285, -58.4634],
  Caballito: [-34.6186, -58.4403],
}

export default function DriverDashboard() {
  const navigate = useNavigate()
  const [driver, setDriver] = useState(null)
  const [trips, setTrips] = useState([])
  const [pendingReviewTrip, setPendingReviewTrip] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedBarrio, setSelectedBarrio] = useState('')
  const [locationMsg, setLocationMsg] = useState('')
  const [detectingLocation, setDetectingLocation] = useState(false)
  const intervalRef = useRef(null)

  const loadData = async () => {
    try {
      const [driverRes, tripsRes, historyRes] = await Promise.all([getDriverMe(), getMyTrips(), getTripHistory()])
      setDriver(driverRes.data)
      setTrips(tripsRes.data)
      const reviewTrip = historyRes.data.find(
        (trip) => trip.estado === 'finalizado' && trip.estado_pago === 'aprobado' && !trip.mi_resena
      )
      setPendingReviewTrip(reviewTrip || null)
    } catch {
      setError('Error al cargar datos')
    }
  }

  useEffect(() => {
    loadData()
    intervalRef.current = setInterval(loadData, 5000)
    return () => clearInterval(intervalRef.current)
  }, [])

  const changeStatus = async (estado) => {
    setLoading(true)
    try {
      await updateDriverStatus(estado)
      setDriver((d) => ({ ...d, estado }))
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cambiar estado')
    } finally {
      setLoading(false)
    }
  }

  const setLocation = async (barrio) => {
    const [lat, lon] = BARRIOS[barrio]
    setSelectedBarrio(barrio)
    try {
      await updateDriverLocation(lat, lon)
      setDriver((d) => ({ ...d, latitud_actual: lat, longitud_actual: lon }))
      setLocationMsg(`Ubicacion actualizada: ${barrio}`)
      setTimeout(() => setLocationMsg(''), 3000)
    } catch {
      setLocationMsg('Error al actualizar ubicacion')
    }
  }

  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      setLocationMsg('La geolocalizacion no esta disponible en este navegador')
      return
    }

    setDetectingLocation(true)
    setLocationMsg('')

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        setSelectedBarrio('')
        try {
          await updateDriverLocation(latitude, longitude)
          setDriver((d) => ({ ...d, latitud_actual: latitude, longitud_actual: longitude }))
          setLocationMsg('Ubicacion actual del dispositivo registrada')
        } catch {
          setLocationMsg('Error al guardar la ubicacion actual')
        } finally {
          setDetectingLocation(false)
        }
      },
      (geoError) => {
        if (geoError.code === geoError.PERMISSION_DENIED) {
          setLocationMsg('Permiso de ubicacion denegado. Habilitalo en el navegador.')
        } else if (geoError.code === geoError.POSITION_UNAVAILABLE) {
          setLocationMsg('No se pudo obtener la ubicacion actual.')
        } else if (geoError.code === geoError.TIMEOUT) {
          setLocationMsg('Se agoto el tiempo para obtener la ubicacion.')
        } else {
          setLocationMsg('Error al obtener la ubicacion del dispositivo')
        }
        setDetectingLocation(false)
      },
      {
        enableHighAccuracy: true,
        timeout: 8000,
        maximumAge: 0,
      }
    )
  }

  if (error && !driver) return <div className="max-w-2xl mx-auto px-4 py-10 text-red-500">{error}</div>
  if (!driver) return <div className="max-w-2xl mx-auto px-4 py-10 text-gray-400">Cargando...</div>

  return (
    <div className="max-w-2xl mx-auto px-4 py-10 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Panel del conductor</h1>
        <p className="text-gray-500 text-sm">Hola, {driver.nombre}</p>
      </div>

      <div className="bg-white border rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">Tu estado</h2>
          <span className={`text-sm px-3 py-1 rounded-full font-medium capitalize border ${ESTADO_COLORS[driver.estado]}`}>
            {driver.estado}
          </span>
        </div>
        <div className="flex gap-2 flex-wrap">
          {ESTADOS.filter((e) => e !== driver.estado).map((e) => (
            <button
              key={e}
              onClick={() => changeStatus(e)}
              disabled={loading}
              className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 capitalize"
            >
              Cambiar a {e}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white border rounded-xl p-5">
        <h2 className="font-semibold mb-1">Tu ubicacion</h2>
        <p className="text-xs text-gray-500 mb-3">Necesitas tener una ubicacion activa para recibir viajes</p>
        {driver.latitud_actual ? (
          <p className="text-sm text-green-600 mb-3">
            Posicion activa: {selectedBarrio || `${driver.latitud_actual}, ${driver.longitud_actual}`}
          </p>
        ) : (
          <p className="text-sm text-red-500 mb-3">Sin ubicacion - no recibiras viajes asignados</p>
        )}
        <button
          onClick={useCurrentLocation}
          disabled={detectingLocation}
          className="w-full mb-3 bg-black text-white py-2 rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
        >
          {detectingLocation ? 'Detectando ubicacion...' : 'Usar ubicacion actual del dispositivo'}
        </button>
        <div className="flex flex-wrap gap-2">
          {Object.keys(BARRIOS).map((barrio) => (
            <button
              key={barrio}
              onClick={() => setLocation(barrio)}
              className="px-3 py-1 rounded-full text-sm border transition border-gray-300 hover:border-black hover:bg-gray-50"
            >
              {barrio}
            </button>
          ))}
        </div>
        {locationMsg && <p className="text-sm text-green-600 mt-2">{locationMsg}</p>}

        {driver.latitud_actual && (
          <TripMap
            origin={{
              lat: driver.latitud_actual,
              lon: driver.longitud_actual,
              label: '<b>Tu posicion actual</b>',
            }}
            className="mt-4 h-48"
          />
        )}
      </div>

      <Link
        to="/trips/history"
        className="block w-full border text-center py-3 rounded-xl text-sm font-medium hover:bg-gray-50"
      >
        Ver historial de viajes
      </Link>

      {pendingReviewTrip && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
          <p className="text-sm font-semibold text-blue-800 mb-1">Tenes una resena pendiente</p>
          <p className="text-sm text-blue-700 mb-4">
            El viaje #{pendingReviewTrip.id_viaje} ya fue pagado. Ahora podes calificar al pasajero.
          </p>
          <Link
            to={`/trips/${pendingReviewTrip.id_viaje}/review`}
            className="inline-block bg-black text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-800"
          >
            Calificar pasajero
          </Link>
        </div>
      )}

      <div className="bg-white border rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">Viajes asignados</h2>
          <span className="text-xs text-gray-400">Se actualiza cada 5s</span>
        </div>

        {trips.length === 0 ? (
          <p className="text-sm text-gray-400 py-4 text-center">
            No tenes viajes activos en este momento
          </p>
        ) : (
          <div className="space-y-3">
            {trips.map((trip) => {
              const st = STATUS_LABELS[trip.estado] || STATUS_LABELS.pendiente
              return (
                <button
                  key={trip.id_viaje}
                  onClick={() => navigate(`/trips/${trip.id_viaje}`)}
                  className="w-full text-left border rounded-xl p-4 hover:bg-gray-50 transition"
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-medium text-sm">Viaje #{trip.id_viaje}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${st.color}`}>{st.label}</span>
                  </div>
                  <p className="text-xs text-gray-500">Origen: {trip.latitud_inicio}, {trip.longitud_inicio}</p>
                  <p className="text-xs text-gray-500">Destino: {trip.latitud_destino}, {trip.longitud_destino}</p>
                  {trip.distancia_km && <p className="text-xs text-gray-400 mt-1">{trip.distancia_km} km</p>}
                  <p className="text-xs text-blue-600 mt-2 font-medium">Toca para ver y gestionar</p>
                </button>
              )
            })}
          </div>
        )}
      </div>

      <div className="bg-white border rounded-xl p-5">
        <h2 className="font-semibold mb-3 text-gray-700">Informacion</h2>
        <div className="space-y-2 text-sm text-gray-600">
          <Row label="Licencia" value={driver.nro_licencia} />
          <Row label="Calificacion" value={`* ${driver.calificacion_promedio}`} />
          <Row label="Email" value={driver.email} />
        </div>
      </div>
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
