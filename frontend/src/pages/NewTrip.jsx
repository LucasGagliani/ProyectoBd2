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
    if (field === 'origen') {
      setForm(f => ({ ...f, origen: barrio, latitud_inicio: lat, longitud_inicio: lon }))
    } else {
      setForm(f => ({ ...f, destino: barrio, latitud_destino: lat, longitud_destino: lon }))
    }
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
      }
      if (form.distancia_km) payload.distancia_km = parseFloat(form.distancia_km)
      if (form.tiempo_minutos) payload.tiempo_minutos = parseInt(form.tiempo_minutos)

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
          <label className="block font-medium mb-3">Datos opcionales</label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Distancia (km)</label>
              <input type="number" step="0.1" min="0" value={form.distancia_km}
                onChange={e => setForm(f => ({ ...f, distancia_km: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black"
                placeholder="ej: 5.2" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Tiempo (min)</label>
              <input type="number" min="0" value={form.tiempo_minutos}
                onChange={e => setForm(f => ({ ...f, tiempo_minutos: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black"
                placeholder="ej: 15" />
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
