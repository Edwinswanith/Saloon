import React from 'react'
import ContentLoader from 'react-content-loader'

// Table Skeleton - For data tables with rows
export const TableSkeleton = ({ rows = 5, columns = 5 }) => {
  return (
    <div style={{ width: '100%' }}>
      {[...Array(rows)].map((_, rowIndex) => (
        <ContentLoader
          key={rowIndex}
          speed={2}
          width="100%"
          height={60}
          backgroundColor="#f3f4f6"
          foregroundColor="#e5e7eb"
          style={{ marginBottom: '8px' }}
        >
          {[...Array(columns)].map((_, colIndex) => (
            <rect
              key={colIndex}
              x={`${(colIndex * 100) / columns}%`}
              y="15"
              rx="4"
              ry="4"
              width={`${90 / columns}%`}
              height="30"
            />
          ))}
        </ContentLoader>
      ))}
    </div>
  )
}

// Card Skeleton - For dashboard cards and panels
export const CardSkeleton = ({ height = 200 }) => {
  return (
    <ContentLoader
      speed={2}
      width="100%"
      height={height}
      backgroundColor="#f3f4f6"
      foregroundColor="#e5e7eb"
    >
      <rect x="20" y="20" rx="4" ry="4" width="60%" height="24" />
      <rect x="20" y="60" rx="4" ry="4" width="40%" height="16" />
      <rect x="20" y="100" rx="8" ry="8" width="90%" height={height - 120} />
    </ContentLoader>
  )
}

// Form Skeleton - For modal forms
export const FormSkeleton = ({ fields = 4 }) => {
  return (
    <div style={{ width: '100%', padding: '20px' }}>
      {[...Array(fields)].map((_, index) => (
        <ContentLoader
          key={index}
          speed={2}
          width="100%"
          height={80}
          backgroundColor="#f3f4f6"
          foregroundColor="#e5e7eb"
          style={{ marginBottom: '12px' }}
        >
          <rect x="0" y="0" rx="4" ry="4" width="30%" height="16" />
          <rect x="0" y="28" rx="4" ry="4" width="100%" height="40" />
        </ContentLoader>
      ))}
    </div>
  )
}

// Stat Skeleton - For dashboard stat cards
export const StatSkeleton = ({ count = 4 }) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(count, 4)}, 1fr)`, gap: '16px', width: '100%' }}>
      {[...Array(count)].map((_, index) => (
        <ContentLoader
          key={index}
          speed={2}
          width="100%"
          height={120}
          backgroundColor="#f3f4f6"
          foregroundColor="#e5e7eb"
        >
          <rect x="20" y="20" rx="4" ry="4" width="60%" height="16" />
          <rect x="20" y="50" rx="4" ry="4" width="80%" height="32" />
          <rect x="20" y="90" rx="4" ry="4" width="40%" height="14" />
        </ContentLoader>
      ))}
    </div>
  )
}

// List Skeleton - For simple lists
export const ListSkeleton = ({ items = 5 }) => {
  return (
    <div style={{ width: '100%' }}>
      {[...Array(items)].map((_, index) => (
        <ContentLoader
          key={index}
          speed={2}
          width="100%"
          height={70}
          backgroundColor="#f3f4f6"
          foregroundColor="#e5e7eb"
          style={{ marginBottom: '8px' }}
        >
          <circle cx="35" cy="35" r="20" />
          <rect x="70" y="20" rx="4" ry="4" width="60%" height="16" />
          <rect x="70" y="44" rx="4" ry="4" width="40%" height="12" />
        </ContentLoader>
      ))}
    </div>
  )
}

// Chart Skeleton - For chart placeholders
export const ChartSkeleton = ({ height = 300 }) => {
  return (
    <ContentLoader
      speed={2}
      width="100%"
      height={height}
      backgroundColor="#f3f4f6"
      foregroundColor="#e5e7eb"
    >
      <rect x="40" y="20" rx="4" ry="4" width="200" height="20" />
      <rect x="40" y={height - 30} rx="0" ry="0" width="2" height={height - 80} />
      <rect x="40" y={height - 30} rx="0" ry="0" width="90%" height="2" />
      
      {[...Array(6)].map((_, index) => (
        <rect
          key={index}
          x={60 + index * 100}
          y={80 + Math.random() * 100}
          rx="4"
          ry="4"
          width="60"
          height={height - 130 - Math.random() * 100}
        />
      ))}
    </ContentLoader>
  )
}

export default {
  TableSkeleton,
  CardSkeleton,
  FormSkeleton,
  StatSkeleton,
  ListSkeleton,
  ChartSkeleton
}

