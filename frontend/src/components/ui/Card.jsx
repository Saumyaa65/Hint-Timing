import React from 'react';
import clsx from 'clsx';

export default function Card({ children, className = '', variant = 'default', as: Component = 'div', ...props }) {
  const variants = {
    default: 'bg-white dark:bg-gray-800 shadow-soft',
    hover: 'bg-white dark:bg-gray-800 shadow-soft hover:shadow-md transition-shadow duration-200',
    interactive: 'bg-white dark:bg-gray-800 shadow-soft hover:shadow-md transition-all duration-200 hover:-translate-y-1',
  };

  return (
    <Component
      className={clsx(
        'rounded-xl overflow-hidden',
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

// Sub-components for consistent card layout
Card.Header = function CardHeader({ children, className = '', ...props }) {
  return (
    <div className={clsx('px-6 py-4 border-b border-gray-100 dark:border-gray-700', className)} {...props}>
      {children}
    </div>
  );
};

Card.Body = function CardBody({ children, className = '', ...props }) {
  return (
    <div className={clsx('px-6 py-4', className)} {...props}>
      {children}
    </div>
  );
};

Card.Footer = function CardFooter({ children, className = '', ...props }) {
  return (
    <div className={clsx('px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-100 dark:border-gray-700', className)} {...props}>
      {children}
    </div>
  );
};