import api from './client'

export const createTrip = (data) => api.post('/trips', data)
export const getMyTrips = () => api.get('/trips/my')
export const getTrip = (id) => api.get(`/trips/${id}`)
export const getTripStatus = (id) => api.get(`/trips/${id}/status`)
export const updateTripStatus = (id, estado) => api.put(`/trips/${id}/status`, { estado })
export const getTripFare = (id) => api.get(`/trips/${id}/fare`)
