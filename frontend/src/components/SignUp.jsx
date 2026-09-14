import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import authService from '../services/authService';
import Button from './Button';
import Loader from './Loader';

export default function SignUp({ onSignIn }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generalError, setGeneralError] = useState('');
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear errors when typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };
  
  const validate = () => {
    const newErrors = {};
    
    // Username validation
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }
    
    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^\S+@\S+\.\S+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }
    
    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    // Confirm password validation
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setGeneralError('');
    
    // Validate form
    if (!validate()) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      const userData = await authService.signUp(formData.username, formData.email, formData.password);
      if (userData) {
        onSignIn(userData);
      }
    } catch (error) {
      console.error('Signup error:', error);
      setGeneralError(
        error.response?.data?.message || 
        'Failed to create account. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="min-h-full flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary-600">
            <polyline points="16 18 22 12 16 6"></polyline>
            <polyline points="8 6 2 12 8 18"></polyline>
          </svg>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Create your account
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Already have an account?{' '}
          <Link to="/signin" className="font-medium text-primary-600 hover:text-primary-500">
            Sign in
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {generalError && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              {generalError}
            </div>
          )}
          
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                Username
              </label>
              <div className="mt-1">
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={formData.username}
                  onChange={handleChange}
                  className={`
                    appearance-none block w-full px-3 py-2 border rounded-md shadow-sm
                    focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm
                    ${errors.username ? 'border-red-300' : 'border-gray-300'}
                  `}
                />
                {errors.username && (
                  <p className="mt-2 text-sm text-red-600">{errors.username}</p>
                )}
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className={`
                    appearance-none block w-full px-3 py-2 border rounded-md shadow-sm
                    focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm
                    ${errors.email ? 'border-red-300' : 'border-gray-300'}
                  `}
                />
                {errors.email && (
                  <p className="mt-2 text-sm text-red-600">{errors.email}</p>
                )}
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className={`
                    appearance-none block w-full px-3 py-2 border rounded-md shadow-sm
                    focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm
                    ${errors.password ? 'border-red-300' : 'border-gray-300'}
                  `}
                />
                {errors.password && (
                  <p className="mt-2 text-sm text-red-600">{errors.password}</p>
                )}
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Confirm Password
              </label>
              <div className="mt-1">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={`
                    appearance-none block w-full px-3 py-2 border rounded-md shadow-sm
                    focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm
                    ${errors.confirmPassword ? 'border-red-300' : 'border-gray-300'}
                  `}
                />
                {errors.confirmPassword && (
                  <p className="mt-2 text-sm text-red-600">{errors.confirmPassword}</p>
                )}
              </div>
            </div>

            <div>
              <Button
                type="submit"
                fullWidth
                loading={isSubmitting}
                disabled={isSubmitting}
              >
                Create account
              </Button>
            </div>
          </form>
          
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Or sign up with</span>
              </div>
            </div>

            <div className="mt-6">
              <button
                type="button"
                className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12.0003 2C14.4701 2 16.6195 2.99 18.1096 4.9C18.0796 4.93 15.6303 7.94 15.6303 7.94L16.5448 8.81L12.0003 8.81L12.0003 5.63L13.1193 5.63C12.0799 4.92 11.0904 4.65 10.0909 4.65C7.37047 4.65 5.14047 7.24 5.14047 10.16C5.14047 13.08 7.37047 15.67 10.0909 15.67C11.3896 15.67 12.3793 15.23 13.0791 14.67C14.0686 13.87 14.5037 12.67 14.6537 11.77L17.4528 11.77C17.1532 15.01 14.0588 18.32 10.0909 18.32C5.85131 18.32 2.34082 14.62 2.34082 10.16C2.34082 5.7 5.85131 2 10.0909 2H12.0003ZM20.8611 11.77V9.5H18.9319V11.77H16.8027V13.82H18.9319V16.09H20.8611V13.82H22.9903V11.77H20.8611Z" />
                </svg>
                <span>Sign up with Google</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}