import api from './client'

export const loginUser = (email, password) =>
  api.post('/auth/login', { email, contrasena: password })

export const registerUsuario = (data) =>
  api.post('/auth/register/usuario', data)

export const registerConductor = (data) =>
  api.post('/auth/register/conductor', data)

export const logout = () =>
  api.post('/auth/logout')
