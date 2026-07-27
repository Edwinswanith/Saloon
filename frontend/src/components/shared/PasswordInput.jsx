import React, { useState } from 'react'
import { FaEye, FaEyeSlash } from 'react-icons/fa'

/**
 * Password input with a show/hide eye toggle.
 * Drop-in replacement for a bare <input type="password" />.
 * `className` is applied to the inner <input> (so existing input styles like
 * `.form-input` keep working); the wrapper uses `wrapperClassName`.
 * All other props are forwarded to the <input>.
 */
const PasswordInput = ({
  value,
  onChange,
  placeholder,
  required = false,
  minLength,
  autoComplete = 'current-password',
  disabled = false,
  className = '',
  wrapperClassName = '',
  style,
  id,
  name,
  ...rest
}) => {
  const [visible, setVisible] = useState(false)

  return (
    <div
      className={`password-input-wrapper ${wrapperClassName}`}
      style={{ position: 'relative', display: 'block', ...style }}
    >
      <input
        id={id}
        name={name}
        type={visible ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        minLength={minLength}
        autoComplete={autoComplete}
        disabled={disabled}
        className={className}
        style={{
          width: '100%',
          paddingRight: '40px',
        }}
        {...rest}
      />
      <button
        type="button"
        onClick={() => setVisible(v => !v)}
        tabIndex={-1}
        aria-label={visible ? 'Hide password' : 'Show password'}
        title={visible ? 'Hide password' : 'Show password'}
        disabled={disabled}
        style={{
          position: 'absolute',
          right: 10,
          top: '50%',
          transform: 'translateY(-50%)',
          background: 'transparent',
          border: 'none',
          cursor: disabled ? 'not-allowed' : 'pointer',
          padding: 4,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#6b7280',
          fontSize: 14,
          minWidth: 'auto',
          minHeight: 'auto',
          lineHeight: 1,
          zIndex: 2,
        }}
      >
        {visible ? <FaEyeSlash /> : <FaEye />}
      </button>
    </div>
  )
}

export default PasswordInput
