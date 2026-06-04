import { createContext, useContext, useState } from 'react'
import { logout as apiLogout } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token') || null)
  const [role, setRole] = useState(localStorage.getItem('role') || null)
  const [userId, setUserId] = useState(localStorage.getItem('userId') || null)

  const login = (tokenValue, roleValue, userIdValue) => {
    localStorage.setItem('token', tokenValue)
    localStorage.setItem('role', roleValue)
    localStorage.setItem('userId', userIdValue)
    setToken(tokenValue)
    setRole(roleValue)
    setUserId(userIdValue)
  }

  const logout = async () => {
    try { await apiLogout() } catch {}
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('userId')
    setToken(null)
    setRole(null)
    setUserId(null)
  }

  return (
    <AuthContext.Provider value={{ token, role, userId, login, logout, isAuth: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
