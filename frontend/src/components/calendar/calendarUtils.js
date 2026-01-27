/**
 * Calendar utility functions for date range calculations and formatting
 */

/**
 * Get the Monday of the week containing the given date
 * @param {Date|string} date - Date object or ISO date string
 * @returns {Date} Monday of the week
 */
export const getWeekStart = (date) => {
  const d = new Date(date)
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1) // Adjust when day is Sunday
  return new Date(d.setDate(diff))
}

/**
 * Get the first day of the month containing the given date
 * @param {Date|string} date - Date object or ISO date string
 * @returns {Date} First day of the month
 */
export const getMonthStart = (date) => {
  const d = new Date(date)
  return new Date(d.getFullYear(), d.getMonth(), 1)
}

/**
 * Get the last day of the month containing the given date
 * @param {Date|string} date - Date object or ISO date string
 * @returns {Date} Last day of the month
 */
export const getMonthEnd = (date) => {
  const d = new Date(date)
  return new Date(d.getFullYear(), d.getMonth() + 1, 0)
}

/**
 * Add days to a date
 * @param {Date|string} date - Date object or ISO date string
 * @param {number} days - Number of days to add (can be negative)
 * @returns {Date} New date
 */
export const addDays = (date, days) => {
  const d = new Date(date)
  d.setDate(d.getDate() + days)
  return d
}

/**
 * Add months to a date
 * @param {Date|string} date - Date object or ISO date string
 * @param {number} months - Number of months to add (can be negative)
 * @returns {Date} New date
 */
export const addMonths = (date, months) => {
  const d = new Date(date)
  d.setMonth(d.getMonth() + months)
  return d
}

/**
 * Format date to ISO string (YYYY-MM-DD)
 * @param {Date|string} date - Date object or ISO date string
 * @returns {string} ISO date string
 */
export const formatDateISO = (date) => {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Calculate date range based on view type and selected date
 * @param {string} view - 'day' | 'week' | 'month'
 * @param {Date|string} selectedDate - Selected date
 * @returns {{fromDate: string, toDate: string}} Date range as ISO strings
 */
export const getDateRangeForView = (view, selectedDate) => {
  const date = new Date(selectedDate)
  
  switch (view) {
    case 'day':
      return {
        fromDate: formatDateISO(date),
        toDate: formatDateISO(date)
      }
    
    case 'week': {
      const weekStart = getWeekStart(date)
      const weekEnd = addDays(weekStart, 6)
      return {
        fromDate: formatDateISO(weekStart),
        toDate: formatDateISO(weekEnd)
      }
    }
    
    case 'month': {
      const monthStart = getMonthStart(date)
      const monthEnd = getMonthEnd(date)
      return {
        fromDate: formatDateISO(monthStart),
        toDate: formatDateISO(monthEnd)
      }
    }
    
    default:
      return {
        fromDate: formatDateISO(date),
        toDate: formatDateISO(date)
      }
  }
}

/**
 * Format header text based on view type and date range
 * @param {string} view - 'day' | 'week' | 'month'
 * @param {string} fromDate - ISO date string
 * @param {string} toDate - ISO date string
 * @returns {string} Formatted header text
 */
export const formatHeaderText = (view, fromDate, toDate) => {
  const months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
  ]
  
  const from = new Date(fromDate)
  const to = new Date(toDate)
  
  switch (view) {
    case 'day': {
      const monthName = months[from.getMonth()]
      const day = from.getDate()
      const year = from.getFullYear()
      return `${monthName} ${day}, ${year}`
    }
    
    case 'week': {
      const fromMonth = months[from.getMonth()]
      const fromDay = from.getDate()
      const fromYear = from.getFullYear()
      const toMonth = months[to.getMonth()]
      const toDay = to.getDate()
      const toYear = to.getFullYear()
      
      if (fromYear === toYear) {
        if (fromMonth === toMonth) {
          return `${fromMonth} ${fromDay} – ${toDay}, ${fromYear}`
        } else {
          return `${fromMonth} ${fromDay} – ${toMonth} ${toDay}, ${fromYear}`
        }
      } else {
        return `${fromMonth} ${fromDay}, ${fromYear} – ${toMonth} ${toDay}, ${toYear}`
      }
    }
    
    case 'month': {
      const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ]
      const monthName = monthNames[from.getMonth()]
      const year = from.getFullYear()
      return `${monthName} ${year}`
    }
    
    default:
      return formatHeaderText('day', fromDate, toDate)
  }
}

/**
 * Navigate date based on view type and direction
 * @param {string} view - 'day' | 'week' | 'month'
 * @param {Date|string} selectedDate - Current selected date
 * @param {string} direction - 'prev' | 'next' | 'today'
 * @returns {string} New date as ISO string
 */
export const navigateDate = (view, selectedDate, direction) => {
  const date = new Date(selectedDate)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  if (direction === 'today') {
    return formatDateISO(today)
  }
  
  switch (view) {
    case 'day':
      if (direction === 'prev') {
        return formatDateISO(addDays(date, -1))
      } else if (direction === 'next') {
        return formatDateISO(addDays(date, 1))
      }
      break
    
    case 'week': {
      if (direction === 'prev') {
        return formatDateISO(addDays(date, -7))
      } else if (direction === 'next') {
        return formatDateISO(addDays(date, 7))
      }
      break
    }
    
    case 'month':
      if (direction === 'prev') {
        return formatDateISO(addMonths(date, -1))
      } else if (direction === 'next') {
        return formatDateISO(addMonths(date, 1))
      }
      break
  }
  
  return formatDateISO(date)
}

/**
 * Get all dates in a date range
 * @param {string} fromDate - ISO date string
 * @param {string} toDate - ISO date string
 * @returns {string[]} Array of ISO date strings
 */
export const getDatesInRange = (fromDate, toDate) => {
  const dates = []
  const start = new Date(fromDate)
  const end = new Date(toDate)
  
  const current = new Date(start)
  while (current <= end) {
    dates.push(formatDateISO(current))
    current.setDate(current.getDate() + 1)
  }
  
  return dates
}

/**
 * Get all days in a week starting from Monday
 * @param {Date|string} date - Date in the week
 * @returns {string[]} Array of ISO date strings for the week
 */
export const getWeekDates = (date) => {
  const weekStart = getWeekStart(date)
  return getDatesInRange(formatDateISO(weekStart), formatDateISO(addDays(weekStart, 6)))
}

/**
 * Get all days in a month
 * @param {Date|string} date - Date in the month
 * @returns {string[]} Array of ISO date strings for the month
 */
export const getMonthDates = (date) => {
  const monthStart = getMonthStart(date)
  const monthEnd = getMonthEnd(date)
  return getDatesInRange(formatDateISO(monthStart), formatDateISO(monthEnd))
}

/**
 * Get month grid dates (includes days from previous/next month to fill the grid)
 * @param {Date|string} date - Date in the month
 * @returns {string[]} Array of ISO date strings for the month grid (typically 35 or 42 days)
 */
export const getMonthGridDates = (date) => {
  const monthStart = getMonthStart(date)
  const monthEnd = getMonthEnd(date)
  
  // Get the first Monday of the grid (might be in previous month)
  const firstDay = monthStart.getDay()
  const daysToSubtract = firstDay === 0 ? 6 : firstDay - 1 // Convert Sunday (0) to 6
  const gridStart = addDays(monthStart, -daysToSubtract)
  
  // Get the last Sunday of the grid (might be in next month)
  const lastDay = monthEnd.getDay()
  const daysToAdd = lastDay === 0 ? 0 : 7 - lastDay
  const gridEnd = addDays(monthEnd, daysToAdd)
  
  return getDatesInRange(formatDateISO(gridStart), formatDateISO(gridEnd))
}

