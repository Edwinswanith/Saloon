/**
 * Ant Design Theme Configuration
 * Customizes Ant Design components to match salon management system design
 */

export const antdTheme = {
  token: {
    // Primary color (matches your existing primary color)
    colorPrimary: '#0F766E',
    colorSuccess: '#10b981',
    colorWarning: '#f59e0b',
    colorError: '#ef4444',
    colorInfo: '#3b82f6',
    
    // Border radius
    borderRadius: 8,
    borderRadiusLG: 12,
    borderRadiusSM: 6,
    
    // Font
    fontFamily: "'Inter', 'Segoe UI', 'Roboto', sans-serif",
    fontSize: 14,
    
    // Spacing
    padding: 16,
    paddingLG: 24,
    paddingSM: 12,
    paddingXS: 8,
    
    // Shadows
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
    boxShadowSecondary: '0 4px 12px rgba(0, 0, 0, 0.12)',
  },
  
  components: {
    // Button customization
    Button: {
      controlHeight: 38,
      fontWeight: 500,
      primaryShadow: '0 2px 0 rgba(102, 126, 234, 0.1)',
    },
    
    // Input customization
    Input: {
      controlHeight: 38,
      paddingInline: 12,
    },
    
    // Select customization
    Select: {
      controlHeight: 38,
    },
    
    // Modal customization
    Modal: {
      borderRadiusLG: 12,
      contentBg: '#ffffff',
      headerBg: '#ffffff',
    },
    
    // Table customization
    Table: {
      headerBg: '#f9fafb',
      headerColor: '#374151',
      borderColor: '#e5e7eb',
      rowHoverBg: '#f3f4f6',
    },
    
    // Form customization
    Form: {
      labelFontSize: 14,
      labelColor: '#374151',
      itemMarginBottom: 20,
    },
    
    // DatePicker customization
    DatePicker: {
      controlHeight: 38,
    },
  },
}

