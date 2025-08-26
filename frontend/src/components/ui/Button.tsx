import React, { type ReactNode, type ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: 'primary' | 'secondary' | 'success' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  className = '',
  ...props
}) => {
  const baseClasses = 'font-bold rounded-child shadow-child transition-all duration-200 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none'
  
  const variants = {
    primary: 'bg-primary-500 hover:bg-primary-600 text-white focus:ring-primary-500',
    secondary: 'bg-secondary-500 hover:bg-secondary-600 text-white focus:ring-secondary-500',
    success: 'bg-success-500 hover:bg-success-600 text-white focus:ring-success-500',
    danger: 'bg-red-500 hover:bg-red-600 text-white focus:ring-red-500',
  }

  const sizes = {
    sm: 'py-2 px-4 text-child-sm',
    md: 'py-3 px-6 text-child-base',
    lg: 'py-4 px-8 text-child-lg',
  }

  const classes = `${baseClasses} ${variants[variant]} ${sizes[size]} ${className}`

  return (
    <button
      {...props}
      disabled={disabled || isLoading}
      className={classes}
    >
      {isLoading ? (
        <div className="flex items-center justify-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          <span>Loading...</span>
        </div>
      ) : (
        children
      )}
    </button>
  )
}

export default Button