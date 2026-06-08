import api from './client'

export const updateLocation = (data) => api.post('/locations/update', data)
export const getTripLocationHistory = (tripId) => api.get(`/locations/${tripId}/history`)
export const getConductorPosition = (conductorId) => api.get(`/locations/conductor/${conductorId}`)
