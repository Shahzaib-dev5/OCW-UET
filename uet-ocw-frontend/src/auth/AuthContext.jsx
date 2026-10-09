import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { fetchJson, sendJsonRaw } from '../data/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('ocw_access_token') || '')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(token))
  const [viewMode, setViewModeState] = useState(() => localStorage.getItem('ocw_view_mode') || 'student')

  const refreshUser = useCallback(async () => {
    if (!localStorage.getItem('ocw_access_token')) {
      localStorage.removeItem('ocw_view_mode')
      setUser(null)
      setViewModeState('student')
      setLoading(false)
      return null
    }
    try {
      setLoading(true)
      const me = await fetchJson('/auth/me')
      setUser(me)
      return me
    } catch {
      localStorage.removeItem('ocw_access_token')
      localStorage.removeItem('ocw_view_mode')
      setToken('')
      setUser(null)
      setViewModeState('student')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser, token])

  const saveSession = useCallback((payload) => {
    if (payload.access_token) {
      localStorage.setItem('ocw_access_token', payload.access_token)
      setToken(payload.access_token)
    }
    if (payload.data) setUser(payload.data)
  }, [])

  const login = useCallback(async (body) => {
    const payload = await sendJsonRaw('/auth/login', { body })
    saveSession(payload)
    return payload
  }, [saveSession])

  const register = useCallback(async (body) => {
    const payload = await sendJsonRaw('/auth/register', { body })
    saveSession(payload)
    return payload
  }, [saveSession])

  const googleLogin = useCallback(async (credential, returnTo, profile = {}) => {
    const payload = await sendJsonRaw('/auth/google', { body: { credential, return_to: returnTo, ...profile } })
    saveSession(payload)
    return payload
  }, [saveSession])

  const verifyEmailOtp = useCallback(async (body) => {
    const payload = await sendJsonRaw('/auth/verify-email-otp', { body })
    saveSession(payload)
    return payload
  }, [saveSession])

  const logout = useCallback(() => {
    localStorage.removeItem('ocw_access_token')
    localStorage.removeItem('ocw_view_mode')
    setToken('')
    setUser(null)
    setViewModeState('student')
  }, [])

  const setViewMode = useCallback((mode) => {
    const nextMode = mode === 'instructor' ? 'instructor' : 'student'
    localStorage.setItem('ocw_view_mode', nextMode)
    setViewModeState(nextMode)
  }, [])

  const isApprovedInstructor = Boolean(user?.is_approved_instructor)
  const effectiveViewMode = isApprovedInstructor ? viewMode : 'student'

  const value = useMemo(() => ({
    token,
    user,
    loading,
    isAuthenticated: Boolean(user),
    isAdmin: String(user?.role?.name || '').toUpperCase() === 'ADMIN',
    isApprovedInstructor,
    isInstructorMode: effectiveViewMode === 'instructor',
    viewMode: effectiveViewMode,
    setViewMode,
    login,
    register,
    googleLogin,
    verifyEmailOtp,
    logout,
    refreshUser,
  }), [effectiveViewMode, googleLogin, isApprovedInstructor, loading, login, logout, refreshUser, register, setViewMode, token, user, verifyEmailOtp])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside AuthProvider')
  return value
}
