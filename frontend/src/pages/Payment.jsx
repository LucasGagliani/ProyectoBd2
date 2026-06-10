import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getTripFare } from '../api/trips'
import { createPayment, getPaymentByTrip } from '../api/payments'
import { useAuth } from '../context/AuthContext'

const METODOS = ['tarjeta_credito', 'tarjeta_debito', 'billetera_virtual', 'efectivo']
const METODO_LABELS = {
  tarjeta_credito: 'Tarjeta de credito',
  tarjeta_debito: 'Tarjeta de debito',
  billetera_virtual: 'Billetera virtual',
  efectivo: 'Efectivo',
}
const STATUS_COLORS = {
  pendiente: 'text-yellow-600 bg-yellow-50',
  aprobado: 'text-green-600 bg-green-50',
  rechazado: 'text-red-600 bg-red-50',
  reembolsado: 'text-gray-600 bg-gray-100',
}

export default function Payment() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { role } = useAuth()
  const isUsuario = role === 'usuario'

  const [fare, setFare] = useState(null)
  const [payment, setPayment] = useState(null)
  const [metodo, setMetodo] = useState('efectivo')
  const [tarifaAdicional, setTarifaAdicional] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const intervalRef = useRef(null)

  const fetchPayment = async () => {
    try {
      const { data } = await getPaymentByTrip(id)
      setPayment(data)
      if (data.estado_transaccion === 'aprobado') {
        clearInterval(intervalRef.current)
      }
    } catch {
      // 404: aun no existe el pago
    }
  }

  useEffect(() => {
    getTripFare(id).then(({ data }) => setFare(data)).catch(() => {})
    fetchPayment()
    intervalRef.current = setInterval(fetchPayment, 4000)
    return () => clearInterval(intervalRef.current)
  }, [id])

  const handlePay = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await createPayment({
        id_viaje: parseInt(id),
        tarifa_adicional: parseFloat(tarifaAdicional),
        metodo_pago: metodo,
      })
      setPayment(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al registrar el pago')
    } finally {
      setLoading(false)
    }
  }

  const estimatedTotal = fare
    ? Number(fare.tarifa_base) + Number(tarifaAdicional || 0)
    : null

  return (
    <div className="max-w-lg mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold mb-1">Pago - Viaje #{id}</h1>
      <p className="text-gray-500 text-sm mb-8">
        {isUsuario ? 'Elegi tu metodo de pago' : 'Estado del pago del viaje'}
      </p>

      {fare && (
        <div className="bg-white border rounded-xl p-5 mb-6 space-y-2 text-sm">
          <Row label="Tarifa base" value={`$${fare.tarifa_base}`} />
          {fare.distancia_km && <Row label="Distancia" value={`${fare.distancia_km} km`} />}
          {fare.tiempo_minutos && <Row label="Tiempo" value={`${fare.tiempo_minutos} min`} />}
          <div className="border-t pt-2 flex justify-between font-semibold text-base">
            <span>Total estimado</span>
            <span>${fare.monto_total}</span>
          </div>
        </div>
      )}

      {isUsuario && !payment && (
        <div className="space-y-4">
          <div className="bg-white border rounded-xl p-5">
            <label className="block font-medium mb-3">Metodo de pago</label>
            <div className="space-y-2">
              {METODOS.map((m) => (
                <label key={m} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="metodo"
                    value={m}
                    checked={metodo === m}
                    onChange={() => setMetodo(m)}
                    className="accent-black"
                  />
                  <span className="text-sm">{METODO_LABELS[m]}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="bg-white border rounded-xl p-5">
            <label className="block font-medium mb-2">Tarifa adicional ($)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={tarifaAdicional}
              onChange={(e) => setTarifaAdicional(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black"
            />
            <p className="text-xs text-gray-400 mt-1">Peaje, espera u otro cargo extra</p>
            {estimatedTotal != null && (
              <p className="text-sm text-gray-700 mt-3">
                Total final estimado: <strong>${estimatedTotal.toFixed(2)}</strong>
              </p>
            )}
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            onClick={handlePay}
            disabled={loading}
            className="w-full bg-black text-white py-3 rounded-xl font-medium hover:bg-gray-800 disabled:opacity-50"
          >
            {loading ? 'Procesando...' : 'Pagar y cerrar viaje'}
          </button>
        </div>
      )}

      {!isUsuario && !payment && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 text-center">
          <p className="text-yellow-700 font-medium mb-1">Esperando al pasajero</p>
          <p className="text-yellow-600 text-sm">El pasajero aun no registro el pago</p>
        </div>
      )}

      {payment && (
        <div className="space-y-4">
          <div className="bg-white border rounded-xl p-5 space-y-2 text-sm">
            <Row label="Metodo" value={METODO_LABELS[payment.metodo_pago]} />
            <Row label="Monto base" value={`$${payment.monto_base}`} />
            <Row label="Adicional" value={`$${payment.tarifa_adicional}`} />
            <div className="border-t pt-2 flex justify-between font-semibold text-base">
              <span>Total</span>
              <span>${payment.monto_total}</span>
            </div>
            <div className="flex justify-between items-center pt-1">
              <span className="text-gray-500">Estado</span>
              <span className={`text-sm px-3 py-1 rounded-full capitalize font-medium ${STATUS_COLORS[payment.estado_transaccion]}`}>
                {payment.estado_transaccion}
              </span>
            </div>
          </div>

          {payment.estado_transaccion === 'aprobado' && (
            <div className="space-y-3">
              <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
                <p className="text-green-700 font-medium">Pago realizado con exito</p>
                <p className="text-green-600 text-sm mt-1">El viaje quedo completamente cerrado</p>
              </div>
              {isUsuario && (
                <button
                  onClick={() => navigate(`/trips/${id}/review`)}
                  className="w-full bg-black text-white py-3 rounded-xl font-medium hover:bg-gray-800"
                >
                  Dejar resena
                </button>
              )}
            </div>
          )}
        </div>
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
