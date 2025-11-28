import React from 'react';
import { clsx } from 'clsx';

export function Card({ children, className, ...props }) {
  return (
    <div
      className={clsx(
        'rounded-lg border border-transparent shadow-sm',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardContent({ children, className, ...props }) {
  return (
    <div
      className={clsx('p-6', className)}
      {...props}
    >
      {children}
    </div>
  );
}

