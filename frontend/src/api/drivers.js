import api from './client'

export const getDriverMe = () => api.get('/drivers/me')
export const updateDriverStatus = (estado) => api.patch('/drivers/me/estado', { estado })
export const updateDriverLocation = (latitud, longitud) => api.patch('/drivers/me/location', { latitud, longitud })
export const getVehicles = () => api.get('/drivers/me/vehicles')
export const createVehicle = (data) => api.post('/drivers/me/vehicles', data)
export const updateVehicle = (id, data) => api.put(`/drivers/me/vehicles/${id}`, data)
export const deleteVehicle = (id) => api.delete(`/drivers/me/vehicles/${id}`)
