import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { API_BASE_URL } from '../config'

const DEFAULT_NAME = 'Priyanka Nature Cure'

const BusinessContext = createContext(null)

export const useBusiness = () => {
  const ctx = useContext(BusinessContext)
  if (!ctx) {
    // Safe default so components can still render if provider is missing.
    return { businessName: DEFAULT_NAME, logoUrl: '', loading: false, refresh: () => {} }
  }
  return ctx
}

export const BusinessProvider = ({ children }) => {
  const [businessName, setBusinessName] = useState(() => {
    try {
      return sessionStorage.getItem('business_name') || DEFAULT_NAME
    } catch {
      return DEFAULT_NAME
    }
  })
  const [logoUrl, setLogoUrl] = useState(() => {
    try {
      return sessionStorage.getItem('business_logo_url') || ''
    } catch {
      return ''
    }
  })
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE_URL}/api/settings/business`)
      if (!res.ok) return
      const data = await res.json()
      const name = (data && data.name) ? data.name : DEFAULT_NAME
      const logo = (data && data.logo_url) ? data.logo_url : ''
      setBusinessName(name)
      setLogoUrl(logo)
      try {
        sessionStorage.setItem('business_name', name)
        sessionStorage.setItem('business_logo_url', logo)
      } catch {
        // Ignore storage errors (private mode etc.)
      }
    } catch (err) {
      console.warn('[BusinessContext] Failed to load business settings:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const value = { businessName, logoUrl, loading, refresh }

  return (
    <BusinessContext.Provider value={value}>
      {children}
    </BusinessContext.Provider>
  )
}
