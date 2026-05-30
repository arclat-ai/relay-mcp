"use client"

import React from 'react'

export default function Button({children, variant='primary', className='', ...props}: any) {
  const base = 'inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-semibold'
  const variants: Record<string,string> = {
    primary: 'text-white',
    ghost: 'text-[var(--muted)] bg-transparent border border-white/06',
  }
  const style = variant === 'primary' ? {background: 'linear-gradient(90deg, var(--accent), var(--accent-600))'} : {}
  return (
    <button className={`${base} ${variants[variant] || ''} ${className}`} style={style} {...props}>
      {children}
    </button>
  )
}
