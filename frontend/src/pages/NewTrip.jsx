import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createTrip } from '../api/trips'
import TripMap from '../components/TripMap'

const COORDS = {
  'Palermo': [-34.5885, -58.4344],
  'Belgrano': [-34.5587, -58.4580],
  'San Telmo': [-34.6211, -58.3731],
  'Recoleta': [-34.5877, -58.3927],
  'Flores': [-34.6285, -58.4634],
  'Caballito': [-34.6186, -58.4403],
}

const AVERAGE_CITY_SPEED_KMH = 22

function toRadians(value) {
  return (value * Math.PI) / 180
}

function calculateDistanceKm(lat1, lon1, lat2, lon2) {
  const earthRadiusKm = 6371
  const dLat = toRadians(lat2 - lat1)
  const dLon = toRadians(lon2 - lon1)
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(lat1)) *
      Math.cos(toRadians(lat2)) *
      Math.sin(dLon / 2) ** 2

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return earthRadiusKm * c
}

function estimateTripMetrics(origenCoords, destinoCoords) {
  if (!origenCoords || !destinoCoords) {
    return { distancia_km: '', tiempo_minutos: '' }
  }

  const [lat1, lon1] = origenCoords
  const [lat2, lon2] = destinoCoords
  const directDistance = calculateDistanceKm(lat1, lon1, lat2, lon2)
  const urbanDistance = directDistance * 1.25
  const tiempoMinutos = Math.max(5, Math.round((urbanDistance / AVERAGE_CITY_SPEED_KMH) * 60))

  return {
    distancia_km: urbanDistance.toFixed(1),
    tiempo_minutos: String(tiempoMinutos),
  }
}

export default function NewTrip() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    origen: '', destino: '',
    latitud_inicio: '', longitud_inicio: '',
    latitud_destino: '', longitud_destino: '',
    distancia_km: '', tiempo_minutos: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const selectBarrio = (field, barrio) => {
    const [lat, lon] = COORDS[barrio]
    setForm((current) => {
      const nextForm = field === 'origen'
        ? { ...current, origen: barrio, latitud_inicio: lat, longitud_inicio: lon }
        : { ...current, destino: barrio, latitud_destino: lat, longitud_destino: lon }

      const origenCoords = nextForm.origen ? COORDS[nextForm.origen] : null
      const destinoCoords = nextForm.destino ? COORDS[nextForm.destino] : null

      return {
        ...nextForm,
        ...estimateTripMetrics(origenCoords, destinoCoords),
      }
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!form.latitud_inicio || !form.latitud_destino) {
      setError('Seleccioná origen y destino')
      return
    }
    setLoading(true)
    try {
      const payload = {
        latitud_inicio: parseFloat(form.latitud_inicio),
        longitud_inicio: parseFloat(form.longitud_inicio),
        latitud_destino: parseFloat(form.latitud_destino),
        longitud_destino: parseFloat(form.longitud_destino),
        distancia_km: parseFloat(form.distancia_km),
        tiempo_minutos: parseInt(form.tiempo_minutos),
      }

      const { data } = await createTrip(payload)
      navigate(`/trips/${data.id_viaje}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al crear el viaje')
    } finally {
      setLoading(false)
    }
  }

  const BarrioSelector = ({ field, selected }) => (
    <div className="flex flex-wrap gap-2 mt-2">
      {Object.keys(COORDS).map(b => (
        <button key={b} type="button" onClick={() => selectBarrio(field, b)}
          className={`px-3 py-1 rounded-full text-sm border transition ${selected === b ? 'bg-black text-white border-black' : 'border-gray-300 hover:border-black'}`}>
          {b}
        </button>
      ))}
    </div>
  )

  return (
    <div className="max-w-lg mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold mb-1">Pedir viaje</h1>
      <p className="text-gray-500 text-sm mb-8">Seleccioná origen y destino</p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white border rounded-xl p-5">
          <label className="block font-medium mb-1">Origen</label>
          <p className="text-sm text-gray-500 mb-1">Seleccioná un barrio:</p>
          <BarrioSelector field="origen" selected={form.origen} />
          {form.origen && (
            <p className="text-xs text-gray-400 mt-2">{form.latitud_inicio}, {form.longitud_inicio}</p>
          )}
        </div>

        <div className="bg-white border rounded-xl p-5">
          <label className="block font-medium mb-1">Destino</label>
          <p className="text-sm text-gray-500 mb-1">Seleccioná un barrio:</p>
          <BarrioSelector field="destino" selected={form.destino} />
          {form.destino && (
            <p className="text-xs text-gray-400 mt-2">{form.latitud_destino}, {form.longitud_destino}</p>
          )}
        </div>

        <div className="bg-white border rounded-xl p-5">
          <label className="block font-medium mb-3">Estimacion del viaje</label>
          <p className="text-sm text-gray-500 mb-4">
            La distancia y el tiempo se calculan automaticamente al elegir origen y destino.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Distancia estimada</label>
              <div className="w-full border rounded-lg px-3 py-2 text-sm bg-gray-50 text-gray-700">
                {form.distancia_km ? `${form.distancia_km} km` : 'Selecciona un recorrido'}
              </div>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Tiempo estimado</label>
              <div className="w-full border rounded-lg px-3 py-2 text-sm bg-gray-50 text-gray-700">
                {form.tiempo_minutos ? `${form.tiempo_minutos} min` : 'Selecciona un recorrido'}
              </div>
            </div>
          </div>
        </div>

        {/* Preview del recorrido cuando ambos puntos están seleccionados */}
        {form.latitud_inicio && form.latitud_destino && (
          <TripMap
            origin={{ lat: form.latitud_inicio, lon: form.longitud_inicio }}
            destination={{ lat: form.latitud_destino, lon: form.longitud_destino }}
          />
        )}

        {error && <p className="text-red-500 text-sm">{error}</p>}

        <button type="submit" disabled={loading}
          className="w-full bg-black text-white py-3 rounded-xl font-medium hover:bg-gray-800 disabled:opacity-50">
          {loading ? 'Buscando conductor...' : 'Confirmar viaje'}
        </button>
      </form>
    </div>
  )
}
