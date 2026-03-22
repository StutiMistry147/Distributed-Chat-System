import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../services/auth'
import { useAuthStore } from '../store/useAuthStore'

export default function AuthView() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  
  const [mode, setMode] = useState('login') // 'login' or 'register'
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (mode === 'login') {
        const data = await login(email, password)
        // Decode JWT token to get user info
        const payload = JSON.parse(atob(data.access_token.split('.')[1]))
        setAuth(data.access_token, { 
          id: parseInt(payload.sub), 
          username: payload.username, 
          email: payload.email 
        })
        navigate('/')
      } else {
        await register(username, email, password)
        // Auto-login after registration
        const data = await login(email, password)
        // Decode JWT token to get user info
        const payload = JSON.parse(atob(data.access_token.split('.')[1]))
        setAuth(data.access_token, { 
          id: parseInt(payload.sub), 
          username: payload.username, 
          email: payload.email 
        })
        navigate('/')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-space-bg">
      <div className="bg-space-surface p-8 rounded-lg shadow-lg w-96">
        <h2 className="text-2xl font-bold mb-6 text-center text-white">
          {mode === 'login' ? 'Welcome Back' : 'Create an Account'}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium text-space-pale mb-1">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 border border-space-lavender rounded-md focus:outline-none focus:ring-2 focus:ring-space-cyan bg-space-input text-white"
                required
              />
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-space-pale mb-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-space-lavender rounded-md focus:outline-none focus:ring-2 focus:ring-space-cyan bg-space-input text-white"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-space-pale mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-space-lavender rounded-md focus:outline-none focus:ring-2 focus:ring-space-cyan bg-space-input text-white"
              required
            />
          </div>
          
          {error && (
            <div className="text-red-500 text-sm text-center">{error}</div>
          )}
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-space-cyan hover:bg-space-cyan/80 text-space-bg py-2 rounded-md transition-colors disabled:opacity-50"
          >
            {loading ? 'Loading...' : (mode === 'login' ? 'Login' : 'Register')}
          </button>
        </form>
        
        <button
          onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
          className="mt-4 text-sm text-space-purple hover:underline w-full text-center"
        >
          {mode === 'login' 
            ? "Don't have an account? Register" 
            : "Already have an account? Login"}
        </button>
      </div>
    </div>
  )
}