import React from 'react';
import clsx from 'clsx';

export default function Skeleton({ className = '', variant = 'rectangular', animate = true }) {
  const baseClasses = 'bg-gray-200 dark:bg-gray-700';
  
  const variants = {
    rectangular: 'rounded',
    circular: 'rounded-full',
    text: 'rounded',
  };

  return (
    <div
      className={clsx(
        baseClasses,
        variants[variant],
        animate && 'animate-pulse',
        className
      )}
    />
  );
}

// Pre-built skeleton components for common use cases
Skeleton.Text = function SkeletonText({ lines = 1, className = '' }) {
  return (
    <div className={clsx('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={clsx(
            'h-4',
            i === lines - 1 ? 'w-4/5' : 'w-full'
          )}
          variant="text"
        />
      ))}
    </div>
  );
};

Skeleton.Avatar = function SkeletonAvatar({ size = 'md', className = '' }) {
  const sizes = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  };

  return (
    <Skeleton
      variant="circular"
      className={clsx(sizes[size], className)}
    />
  );
};

Skeleton.Card = function SkeletonCard({ className = '' }) {
  return (
    <div className={clsx('space-y-4 rounded-xl p-4', className)}>
      <Skeleton.Avatar size="lg" />
      <Skeleton.Text lines={4} />
    </div>
  );
};