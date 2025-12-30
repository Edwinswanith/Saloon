import React from 'react'
import { motion } from 'framer-motion'

// Page transition wrapper with smooth fade + slide animations
export const PageTransition = ({ children, className = '' }) => {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1] // Smooth easing
      }}
    >
      {children}
    </motion.div>
  )
}

// Modal transition wrapper
export const ModalTransition = ({ children, isOpen }) => {
  if (!isOpen) return null
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{
        duration: 0.2,
        ease: [0.4, 0, 0.2, 1]
      }}
    >
      {children}
    </motion.div>
  )
}

// Card stagger animation wrapper
export const StaggerContainer = ({ children, className = '', staggerDelay = 0.1 }) => {
  return (
    <motion.div
      className={className}
      initial="hidden"
      animate="visible"
      variants={{
        visible: {
          transition: {
            staggerChildren: staggerDelay
          }
        }
      }}
    >
      {children}
    </motion.div>
  )
}

// Individual stagger item
export const StaggerItem = ({ children, className = '' }) => {
  return (
    <motion.div
      className={className}
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: {
          opacity: 1,
          y: 0,
          transition: {
            duration: 0.4,
            ease: [0.4, 0, 0.2, 1]
          }
        }
      }}
    >
      {children}
    </motion.div>
  )
}

// Hover scale animation
export const HoverScale = ({ children, className = '', scale = 1.05 }) => {
  return (
    <motion.div
      className={className}
      whileHover={{ scale }}
      whileTap={{ scale: scale - 0.02 }}
      transition={{
        type: 'spring',
        stiffness: 400,
        damping: 17
      }}
    >
      {children}
    </motion.div>
  )
}

export default PageTransition

