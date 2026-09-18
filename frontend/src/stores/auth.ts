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
  username: string | null
  role: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => {
    const token = getToken()
    const payload = token ? decodeJwt(token) : null
    const valid = payload && payload.exp * 1000 > Date.now()
    return {
      token: valid ? token : null,
      username: valid ? payload!.sub : null,
      role: valid ? payload!.role : null,
    }
  },

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.role === 'admin',
  },

  actions: {
    async login(username: string, password: string) {
      const form = new URLSearchParams()
      form.set('username', username)
      form.set('password', password)
      const { data } = await api.post('/api/v1/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      this.applyToken(data.access_token)
    },

    async register(username: string, password: string) {
      await api.post('/api/v1/auth/register', { username, password })
    },

    applyToken(token: string) {
      const payload = decodeJwt(token)
      if (!payload) throw new Error('Token inválido recibido del servidor.')
      setToken(token)
      this.token = token
      this.username = payload.sub
      this.role = payload.role
    },

    logout() {
      clearToken()
      this.token = null
      this.username = null
      this.role = null
    },
  },
})
