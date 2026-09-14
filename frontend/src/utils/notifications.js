import { toast } from 'react-hot-toast';

const notifications = {
  success: (message) => {
    toast.success(message, {
      style: {
        background: '#f0fdf4',
        color: '#166534',
        border: '1px solid #bbf7d0',
      },
      iconTheme: {
        primary: '#22c55e',
        secondary: '#ffffff',
      },
    });
  },
  error: (message) => {
    toast.error(message, {
      style: {
        background: '#fef2f2',
        color: '#991b1b',
        border: '1px solid #fecaca',
      },
      iconTheme: {
        primary: '#ef4444',
        secondary: '#ffffff',
      },
    });
  },
  warning: (message) => {
    toast(message, {
      icon: '⚠️',
      style: {
        background: '#fffbeb',
        color: '#92400e',
        border: '1px solid #fde68a',
      },
    });
  },
  info: (message) => {
    toast(message, {
      icon: 'ℹ️',
      style: {
        background: '#f0f9ff',
        color: '#075985',
        border: '1px solid #bae6fd',
      },
    });
  },
  loading: (message) => {
    return toast.loading(message, {
      style: {
        background: '#f0f9ff',
        color: '#075985',
        border: '1px solid #bae6fd',
      },
    });
  },
  dismiss: (toastId) => {
    toast.dismiss(toastId);
  },
  promise: async (promise, messages = {}) => {
    return toast.promise(
      promise,
      {
        loading: messages.loading || 'Loading...',
        success: messages.success || 'Success!',
        error: messages.error || 'Error occurred.',
      },
      {
        success: {
          style: {
            background: '#f0fdf4',
            color: '#166534',
            border: '1px solid #bbf7d0',
          },
          iconTheme: {
            primary: '#22c55e',
            secondary: '#ffffff',
          },
        },
        error: {
          style: {
            background: '#fef2f2',
            color: '#991b1b',
            border: '1px solid #fecaca',
          },
          iconTheme: {
            primary: '#ef4444',
            secondary: '#ffffff',
          },
        },
      }
    );
  },
};

export default notifications;