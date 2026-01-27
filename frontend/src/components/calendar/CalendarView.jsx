import { useState, useEffect, useCallback } from 'react'
import { getDateRangeForView, navigateDate } from './calendarUtils'

/**
 * useCalendarView - Custom hook to manage calendar state and date ranges
 * 
 * This hook handles:
 * - Active view (day/week/month)
 * - Selected date
 * - Date range calculation (fromDate/toDate)
 * - Navigation callbacks
 * 
 * @param {string} initialView - Initial view mode ('day' | 'week' | 'month')
 * @param {string|null} initialDate - Initial selected date (ISO string) or null for today
 * @param {Function} onDateRangeChange - Callback when date range changes
 * @returns {Object} Calendar state and handlers
 */
export const useCalendarView = (initialView = 'day', initialDate = null, onDateRangeChange = null) => {
  const today = new Date().toISOString().split('T')[0]
  const [activeView, setActiveView] = useState(initialView)
  const [selectedDate, setSelectedDate] = useState(initialDate || today)
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')

  // Calculate date range when view or selected date changes
  useEffect(() => {
    const range = getDateRangeForView(activeView, selectedDate)
    setFromDate(range.fromDate)
    setToDate(range.toDate)
    
    // Notify parent component of date range change
    if (onDateRangeChange) {
      onDateRangeChange({
        activeView,
        selectedDate,
        fromDate: range.fromDate,
        toDate: range.toDate
      })
    }
  }, [activeView, selectedDate, onDateRangeChange])

  // Handle view change
  const handleViewChange = useCallback((newView) => {
    setActiveView(newView)
    // Date range will be recalculated in useEffect
  }, [])

  // Handle date change
  const handleDateChange = useCallback((newDate) => {
    setSelectedDate(newDate)
    // Date range will be recalculated in useEffect
  }, [])

  // Handle navigation (prev/next/today)
  const handleNavigate = useCallback((direction) => {
    const newDate = navigateDate(activeView, selectedDate, direction)
    setSelectedDate(newDate)
    // Date range will be recalculated in useEffect
  }, [activeView, selectedDate])

  return {
    activeView,
    selectedDate,
    fromDate,
    toDate,
    setActiveView: handleViewChange,
    setSelectedDate: handleDateChange,
    navigate: handleNavigate
  }
}

export default useCalendarView

