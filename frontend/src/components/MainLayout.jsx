import React from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import Navbar from './Navbar';
import authService from '../services/authService';

/**
 * Main layout component that wraps all pages
 * Includes the navbar and handles common layout elements
 */
export default function MainLayout({ children }) {
  const location = useLocation();
  const user = authService.getUser();
  
  // Handle sign out
  const handleSignOut = () => {
    authService.clearUser();
    window.location.href = '/signin'; // Force a full refresh to clear state
  };
  
  // Check if we're on the problem detail page to handle full height
  const isProblemDetailPage = location.pathname.includes('/problems/');
  
  return (
    <div className="flex flex-col min-h-screen bg-gray-50 antialiased">
      {/* Global notification container */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 5000,
          className: '!bg-white !shadow-soft',
          success: {
            className: '!border-l-4 !border-secondary-500',
          },
          error: {
            className: '!border-l-4 !border-error-500',
          },
        }}
      />
      
      {/* Navbar with animation */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <Navbar user={user} onSignOut={handleSignOut} />
      </motion.header>
      
      {/* Main content with page transitions */}
      <main 
        className={`flex-1 transition-all duration-300 ease-in-out ${
          isProblemDetailPage ? 'p-0' : 'py-6 px-4 sm:px-6 lg:px-8'
        }`}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="h-full"
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>
      
      {/* Footer with animation - don't show on problem detail page */}
      <AnimatePresence>
        {!isProblemDetailPage && (
          <motion.footer
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 20, opacity: 0 }}
            className="bg-white border-t border-gray-200 py-4 shadow-inner-soft"
          >
            <div className="max-w-7xl mx-auto px-4">
              <div className="flex flex-col items-center space-y-2">
                <div className="flex items-center space-x-2">
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    width="20" 
                    height="20" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    className="text-primary-600"
                  >
                    <polyline points="16 18 22 12 16 6"></polyline>
                    <polyline points="8 6 2 12 8 18"></polyline>
                  </svg>
                  <span className="font-semibold text-gray-700 tracking-tight">
                    CodeHint
                  </span>
                </div>
                <p className="text-sm text-gray-500">
                  © {new Date().getFullYear()} CodeHint | Intelligent Hint Generation System
                </p>
              </div>
            </div>
          </motion.footer>
        )}
      </AnimatePresence>
    </div>
  );
}