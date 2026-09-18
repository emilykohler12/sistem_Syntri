import { defineStore } from 'pinia'
import { api, clearToken, getToken, setToken } from '@/lib/api'
import type { JwtPayload } from '@/types'

function decodeJwt(token: string): JwtPayload | null {
  try {
    const payload = token.split('.')[1]
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(json) as JwtPayload
  } catch {
    return null
  }
}

interface AuthState {
  token: string | null
  email: string | null
  role: string | null
  permissions: string[]
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => {
    const token = getToken()
    const payload = token ? decodeJwt(token) : null
    const valid = payload && payload.exp * 1000 > Date.now()
    return {
      token: valid ? token : null,
      email: valid ? payload!.sub : null,
      role: valid ? payload!.role : null,
      permissions: valid ? (payload!.permissions ?? []) : [],
    }
  },

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.role === 'admin',
    // Admin ve todo el panel; otro rol solo si tiene alguna capacidad asignada
    canAccessAdmin: (state) => state.role === 'admin' || state.permissions.length > 0,
  },

  actions: {
    hasPermission(capability: string): boolean {
      return this.isAdmin || this.permissions.includes(capability)
    },

    async login(email: string, password: string) {
      // El backend usa OAuth2PasswordRequestForm, que siempre llama al campo
      // "username" por espec — acá viaja el email igual.
      const form = new URLSearchParams()
      form.set('username', email)
      form.set('password', password)
      const { data } = await api.post('/api/v1/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      this.applyToken(data.access_token)
    },

    async register(email: string, password: string) {
      await api.post('/api/v1/auth/register', { email, password })
    },

    async forgotPassword(email: string) {
      await api.post('/api/v1/auth/forgot-password', { email })
    },

    async resetPassword(email: string, code: string, newPassword: string) {
      await api.post('/api/v1/auth/reset-password', { email, code, new_password: newPassword })
    },

    applyToken(token: string) {
      const payload = decodeJwt(token)
      if (!payload) throw new Error('Token inválido recibido del servidor.')
      setToken(token)
      this.token = token
      this.email = payload.sub
      this.role = payload.role
      this.permissions = payload.permissions ?? []
    },

    logout() {
      clearToken()
      this.token = null
      this.email = null
      this.role = null
      this.permissions = []
    },
  },
})
