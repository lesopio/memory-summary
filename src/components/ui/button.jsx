import React from 'react';
import { clsx } from 'clsx';

export function Button({ 
  children, 
  className, 
  onClick, 
  type = 'button',
  ...props 
}) {
  return (
    <button
      type={type}
      className={clsx(
        'inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium',
        'transition-colors focus-visible:outline-none focus-visible:ring-2',
        'focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
        className
      )}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
}

