/**
 * Pinia Auth Store
 * Manages user authentication state
 */

import { defineStore } from 'pinia'
import axios from 'axios'

// Use environment variable for API base URL
// In development: uses vite proxy (empty string)
// In production: uses VITE_API_URL environment variable
const API_BASE = import.meta.env.VITE_API_URL || ''

export const useAuthStore = defineStore('auth', {
    state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
    providers: [],
    loading: false,
    error: null,
    registerSuccess: false
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user,
    availableProviders: (state) => state.providers.filter(p => p.enabled)
  },

  actions: {
    async fetchProviders() {
      try {
        const response = await axios.get(`${API_BASE}/api/auth/providers`)
        this.providers = response.data.providers
      } catch (error) {
        console.error('Failed to fetch providers:', error)
        this.error = 'Failed to load login options'
      }
    },

    async loginWithProvider(provider) {
      this.loading = true
      this.error = null
      try {
        const response = await axios.get(`${API_BASE}/api/auth/login/${provider}`)
        // Redirect to OAuth provider
        window.location.href = response.data.authorization_url
      } catch (error) {
        console.error('Login failed:', error)
        this.error = 'Failed to initiate login'
        this.loading = false
      }
    },

    async loginWithCredentials({ username, password, remember_me = false }) {
      this.loading = true
      this.error = null
      try {
        const response = await axios.post(`${API_BASE}/api/auth/login`, {
          username,
          password,
          remember_me
        })
        
        const { access_token, user } = response.data
        this.token = access_token
        this.user = user
        
        if (user.points !== undefined) {
          user.points = parseFloat(user.points) || 0
        }
        
        if (remember_me) {
          localStorage.setItem('token', access_token)
        } else {
          sessionStorage.setItem('token', access_token)
        }
        
        this.loading = false
        return { success: true }
      } catch (error) {
        console.error('Login failed:', error)
        this.error = error.response?.data?.detail || 'Login failed. Please check your credentials.'
        this.loading = false
        return { success: false, error: this.error }
      }
    },

async register({ username, email, password }) {
      this.loading = true
      this.error = null
      this.registerSuccess = false
      try {
        const response = await axios.post(`${API_BASE}/api/auth/register`, {
          username,
          email,
          password
        })
        // Success - show success on register page
        console.log('Register API success:', response.data)
        this.registerSuccess = true
        this.$router.push('/login?registered=true')
      } catch (error) {
      console.error('Register failed:', error)
      this.error = error.response?.data?.detail || '注册失败，请重试。'
      console.log('Register network response:', error.response?.status, error.response?.data)
      } finally {
        this.loading = false
      }
    },


    async forgotPassword(email) {
      this.loading = true
      this.error = null
      try {
        await axios.post(`${API_BASE}/api/auth/forgot-password`, { email })
        this.error = '重置邮件已发送，请检查邮箱！'
      } catch (error) {
        console.error('Forgot password failed:', error)
        this.error = error.response?.data?.detail || '发送失败，请重试。'
      } finally {
        this.loading = false
      }
    },

    async fetchPointsBalance() {
      if (!this.isAuthenticated) return
      try {
        const response = await axios.get(`${API_BASE}/api/points/balance`, {
          headers: { Authorization: `Bearer ${this.token}` }
        })
        if (this.user) {
          this.user.points = response.data.points
        }
      } catch (error) {
        console.error('Failed to fetch points:', error)
      }
    },

    async buyVirtualPoints(form) {
      if (!this.isAuthenticated) throw new Error('Not authenticated')
      try {
        const response = await axios.post(`${API_BASE}/api/points/buy`, form, {
          headers: { Authorization: `Bearer ${this.token}` }
        })
        this.user.points += form.quantity
        this.error = '购买成功！'
      } catch (error) {
        console.error('Buy failed:', error)
        this.error = error.response?.data?.detail || '购买失败'
        throw error
      }
    },

    async sellVirtualPoints(form) {
      if (!this.isAuthenticated) throw new Error('Not authenticated')
      try {
        const response = await axios.post(`${API_BASE}/api/points/sell`, form, {
          headers: { Authorization: `Bearer ${this.token}` }
        })
        this.user.points -= form.quantity
        this.error = '出售成功！'
      } catch (error) {
        console.error('Sell failed:', error)
        this.error = error.response?.data?.detail || '出售失败'
        throw error
      }
    },

    async fetchCurrentUser() {
      if (!this.token) return null
      
      try {
        const response = await axios.get(`${API_BASE}/api/auth/me`, {
          headers: {
            Authorization: `Bearer ${this.token}`
          }
        })
        this.user = response.data
        return response.data
      } catch (error) {
        console.error('Failed to fetch user:', error)
        this.logout()
        return null
      }
    },

    async setToken(token) {
      this.token = token
      this.loading = true
      localStorage.setItem('token', token)
      await this.fetchCurrentUser()
      this.loading = false
    },

    logout() {
      this.user = null
      this.token = null
      this.loading = false
      this.error = null
      localStorage.removeItem('token')
    },

    clearError() {
      this.error = null
    }
  }
})

