import React, { Fragment } from 'react';
import { Dialog as HeadlessDialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

export default function Dialog({
  isOpen,
  onClose,
  children,
  className = '',
  maxWidth = '2xl',
}) {
  const maxWidthClasses = {
    sm: 'sm:max-w-sm',
    md: 'sm:max-w-md',
    lg: 'sm:max-w-lg',
    xl: 'sm:max-w-xl',
    '2xl': 'sm:max-w-2xl',
    '3xl': 'sm:max-w-3xl',
    '4xl': 'sm:max-w-4xl',
    '5xl': 'sm:max-w-5xl',
    full: 'sm:max-w-full',
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <HeadlessDialog
        as="div"
        className="relative z-50"
        onClose={onClose}
      >
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/25 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <HeadlessDialog.Panel
                className={clsx(
                  'w-full transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all dark:bg-gray-800',
                  maxWidthClasses[maxWidth],
                  className
                )}
              >
                {children}
              </HeadlessDialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </HeadlessDialog>
    </Transition>
  );
}

Dialog.Title = function DialogTitle({ children, className = '' }) {
  return (
    <HeadlessDialog.Title
      as="h3"
      className={clsx(
        'text-lg font-medium leading-6 text-gray-900 dark:text-white',
        className
      )}
    >
      {children}
    </HeadlessDialog.Title>
  );
};

Dialog.Description = function DialogDescription({ children, className = '' }) {
  return (
    <HeadlessDialog.Description
      className={clsx(
        'mt-2 text-sm text-gray-500 dark:text-gray-400',
        className
      )}
    >
      {children}
    </HeadlessDialog.Description>
  );
};

Dialog.CloseButton = function DialogCloseButton({ className = '', ...props }) {
  return (
    <button
      type="button"
      className={clsx(
        'absolute right-4 top-4 rounded-lg p-1 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:text-gray-500 dark:hover:text-gray-400',
        className
      )}
      {...props}
    >
      <span className="sr-only">Close</span>
      <XMarkIcon className="h-5 w-5" />
    </button>
  );
};