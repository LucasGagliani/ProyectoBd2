import { useEffect, useState } from 'react'
import { getVehicles, createVehicle, updateVehicle, deleteVehicle } from '../api/drivers'

const EMPTY_FORM = { marca: '', modelo: '', anio: '', nro_placa: '', color: '', tipo_vehiculo: '', capacidad_pasajeros: '' }

export default function Vehicles() {
  const [vehicles, setVehicles] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const load = () => getVehicles().then(({ data }) => setVehicles(data)).catch(() => {})
  useEffect(() => { load() }, [])

  const openCreate = () => { setForm(EMPTY_FORM); setEditing(null); setShowForm(true); setError('') }
  const openEdit = (v) => {
    setForm({ marca: v.marca, modelo: v.modelo, anio: v.anio, nro_placa: v.nro_placa, color: v.color || '', tipo_vehiculo: v.tipo_vehiculo || '', capacidad_pasajeros: v.capacidad_pasajeros || '' })
    setEditing(v.id_vehiculo); setShowForm(true); setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault(); setError(''); setLoading(true)
    try {
      const payload = { ...form, anio: parseInt(form.anio), capacidad_pasajeros: parseInt(form.capacidad_pasajeros) }
      editing ? await updateVehicle(editing, payload) : await createVehicle(payload)
      setShowForm(false); load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al guardar')
    } finally { setLoading(false) }
  }

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar vehículo?')) return
    try { await deleteVehicle(id); load() } catch {}
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Mis vehículos</h1>
          <p className="text-gray-500 text-sm">Gestioná tu flota</p>
        </div>
        <button onClick={openCreate}
          className="bg-black text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-800">
          + Agregar
        </button>
      </div>

      {vehicles.length === 0 && !showForm && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-lg mb-2">No tenés vehículos registrados</p>
          <button onClick={openCreate} className="text-black underline text-sm">Agregar uno</button>
        </div>
      )}

      <div className="space-y-4 mb-6">
        {vehicles.map(v => (
          <div key={v.id_vehiculo} className="bg-white border rounded-xl p-5">
            <div className="flex justify-between items-start">
              <div>
                <p className="font-semibold">{v.marca} {v.modelo} ({v.anio})</p>
                <p className="text-sm text-gray-500">{v.nro_placa} · {v.color} · {v.tipo_vehiculo}</p>
                <p className="text-sm text-gray-400">{v.capacidad_pasajeros} pasajeros</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => openEdit(v)} className="text-sm text-blue-600 hover:underline">Editar</button>
                <button onClick={() => handleDelete(v.id_vehiculo)} className="text-sm text-red-500 hover:underline">Eliminar</button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {showForm && (
        <div className="bg-white border rounded-xl p-5">
          <h2 className="font-semibold mb-4">{editing ? 'Editar vehículo' : 'Nuevo vehículo'}</h2>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              {[['Marca', 'marca'], ['Modelo', 'modelo'], ['Año', 'anio', 'number'], ['Patente', 'nro_placa'], ['Color', 'color'], ['Tipo', 'tipo_vehiculo'], ['Capacidad', 'capacidad_pasajeros', 'number']].map(([label, key, type = 'text']) => (
                <div key={key} className={key === 'tipo_vehiculo' ? 'col-span-2' : ''}>
                  <label className="block text-sm text-gray-600 mb-1">{label}</label>
                  <input type={type} value={form[key]} required
                    onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black" />
                </div>
              ))}
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <div className="flex gap-2 pt-2">
              <button type="submit" disabled={loading}
                className="flex-1 bg-black text-white py-2 rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-50">
                {loading ? 'Guardando...' : 'Guardar'}
              </button>
              <button type="button" onClick={() => setShowForm(false)}
                className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50">
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
