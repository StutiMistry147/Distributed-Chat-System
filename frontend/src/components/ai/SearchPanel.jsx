import { useState, useEffect, useRef } from 'react'
import api from '../../services/api'
import { useAppStore } from '../../store/useAppStore'
import { format } from 'date-fns'

export default function SearchPanel({ onClose }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const { activeChannelId } = useAppStore()
  const inputRef = useRef(null)

  useEffect(() => {
    // Focus input on mount
    inputRef.current?.focus()
    
    // Handle Escape key
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  useEffect(() => {
    const searchMessages = async () => {
      if (!query.trim() || query.length < 2) {
        setResults([])
        return
      }

      setIsLoading(true)
      setError('')
      
      try {
        const response = await api.post('/ai/search', {
          query: query.trim(),
          channel_id: activeChannelId,
          top_k: 10
        })
        setResults(response.data)
      } catch (err) {
        console.error('Search failed:', err)
        setError(err.response?.data?.detail || 'Failed to search messages')
      } finally {
        setIsLoading(false)
      }
    }

    const debounceTimer = setTimeout(searchMessages, 500)
    return () => clearTimeout(debounceTimer)
  }, [query, activeChannelId])

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return ''
    try {
      return format(new Date(timestamp), 'MMM d, HH:mm')
    } catch {
      return ''
    }
  }

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'bg-green-500'
    if (score >= 0.6) return 'bg-space-cyan'
    if (score >= 0.4) return 'bg-yellow-500'
    return 'bg-gray-500'
  }

  return (
    <div 
      className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center"
      onClick={handleBackdropClick}
    >
      <div className="w-full max-w-2xl mt-20 mx-4 bg-[var(--surface)] rounded-lg shadow-xl border border-[var(--border)] animate-slide-down">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">
            Search Messages
          </h3>
          <button
            onClick={onClose}
            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Search Input */}
        <div className="p-4 border-b border-[var(--border)]">
          <div className="relative">
            <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for messages... (min. 2 characters)"
              className="w-full pl-10 pr-4 py-2 bg-[var(--input)] text-[var(--text-primary)] rounded-lg focus:outline-none focus:ring-2 focus:ring-space-cyan"
            />
          </div>
        </div>
        
        {/* Results */}
        <div className="max-h-[60vh] overflow-y-auto p-4 space-y-3">
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <div className="text-[var(--text-secondary)]">Searching...</div>
            </div>
          )}
          
          {error && (
            <div className="flex items-center justify-center py-8">
              <div className="text-red-500">{error}</div>
            </div>
          )}
          
          {!isLoading && !error && query.length >= 2 && results.length === 0 && (
            <div className="flex items-center justify-center py-8">
              <div className="text-[var(--text-secondary)]">No results found</div>
            </div>
          )}
          
          {results.map((result) => (
            <div
              key={result.id}
              className="p-3 rounded-lg bg-[var(--input)] hover:bg-[var(--input)]/80 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 rounded-full bg-space-cyan flex items-center justify-center text-[var(--bg)] font-bold text-xs">
                    {result.username.charAt(0).toUpperCase()}
                  </div>
                  <span className="text-sm font-medium text-[var(--text-primary)]">
                    {result.username}
                  </span>
                  <span className="text-xs text-[var(--text-secondary)]">
                    {formatTimestamp(result.timestamp)}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-[var(--text-secondary)]">
                    {Math.round(result.score * 100)}%
                  </span>
                  <div className="w-16 h-1 bg-[var(--border)] rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${getScoreColor(result.score)} transition-all`}
                      style={{ width: `${result.score * 100}%` }}
                    />
                  </div>
                </div>
              </div>
              <p className="text-sm text-[var(--text-primary)] leading-relaxed">
                {result.content}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}