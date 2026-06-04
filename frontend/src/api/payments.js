import api from './client'

export const createPayment = (data) => api.post('/payments', data)
export const getPaymentByTrip = (tripId) => api.get(`/payments/trip/${tripId}`)
export const getPayment = (id) => api.get(`/payments/${id}`)
export const updatePaymentStatus = (id, estado) =>
  api.patch(`/payments/${id}/status`, { estado_transaccion: estado })
