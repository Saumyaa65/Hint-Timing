import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { UserButton } from '@clerk/clerk-react';
import ThemeToggle from './ThemeToggle';
import apiClient from '../services/apiClient';

export default function Navbar({ user, theme, onToggleTheme }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [streak, setStreak] = useState(0);
  const location = useLocation();
  const profileRef = useRef(null);

  const isActive = (path) => location.pathname === path;

  // Fetch streak if user is logged in
  useEffect(() => {
    if (user) {
      apiClient.get('/analytics/user_dashboard/')
        .then(res => setStreak(res.current_streak || 0))
        .catch(err => console.error("Failed to load streak", err));
    }
  }, [user]);

  // Close profile dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setIsProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navLinks = [
    { label: 'Explore', path: '/' },
    { label: 'Problems', path: '/problems' },
    { label: 'Sheets', path: '/sheets' },
    { label: 'Leaderboard', path: '/leaderboard' },
    { label: 'Forum', path: '/forum' },
  ];

  if (user) {
    navLinks.push({ label: 'My Dashboard', path: '/analytics/me' });
    navLinks.push({ label: 'Admin', path: '/admin/analytics' });
  }

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-xl border-b shadow-lg" style={{
      backgroundColor: 'var(--nav-bg)',
      borderColor: 'var(--border)',
      boxShadow: theme === 'dark' ? '0 4px 30px rgba(0,0,0,0.3)' : '0 4px 30px rgba(0,0,0,0.06)'
    }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">

          {/* ── Logo + Desktop Links ── */}
          <div className="flex items-center gap-10">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/30 group-hover:shadow-indigo-500/50 group-hover:scale-105 transition-all duration-300">
                <svg
                  className="w-5 h-5 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5"
                  />
                </svg>
                <div className="absolute inset-0 rounded-xl bg-gradient-to-t from-transparent to-white/20 pointer-events-none" />
              </div>
              <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent select-none">
                HintCode
              </span>
            </Link>

            {/* Desktop nav links */}
            <div className="hidden md:flex items-center gap-1">
              {navLinks.map(({ label, path }) => (
                <Link
                  key={path}
                  to={path}
                  className={`relative px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive(path)
                      ? 'text-[var(--text-primary)] bg-[var(--accent-glow)]'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--accent-glow)]'
                  }`}
                >
                  {label}
                  {isActive(path) && (
                    <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-0.5 rounded-full bg-gradient-to-r from-indigo-400 to-violet-400" />
                  )}
                </Link>
              ))}
            </div>
          </div>

          {/* ── Right side: theme toggle + user area ── */}
          <div className="flex items-center gap-3">

            {/* Theme Toggle */}
            <ThemeToggle theme={theme} onToggle={onToggleTheme} />

            {/* Streak Counter */}
            {user && (
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-orange-500/10 border border-orange-500/20 rounded-full text-orange-500" title="Daily Streak">
                <span className="text-sm font-bold">{streak}</span>
                <span className="text-base leading-none">🔥</span>
              </div>
            )}

            {/* Desktop user avatar / dropdown */}
            {user && (
              <div className="hidden md:block">
                <UserButton afterSignOutUrl="/" appearance={{ elements: { userButtonAvatarBox: "w-8 h-8 ring-2 ring-[var(--border)]" } }} />
              </div>
            )}

            {/* ── Mobile hamburger button ── */}
            <button
              onClick={() => setIsMobileMenuOpen((v) => !v)}
              className="md:hidden inline-flex items-center justify-center w-10 h-10 rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--accent-glow)] border border-transparent hover:border-[var(--border-hover)] transition-all duration-200"
              aria-label="Toggle menu"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* ── Mobile menu panel ── */}
      <div
        className={`md:hidden overflow-hidden transition-all duration-300 ease-in-out ${
          isMobileMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="backdrop-blur-xl border-t px-4 pt-3 pb-5 space-y-1" style={{ backgroundColor: 'var(--nav-bg)', borderColor: 'var(--border)' }}>
          {navLinks.map(({ label, path }) => (
            <Link
              key={path}
              to={path}
              onClick={() => setIsMobileMenuOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-base font-medium transition-all duration-200 ${
                isActive(path)
                  ? 'text-[var(--text-primary)] bg-[var(--accent-glow)]'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--accent-glow)]'
              }`}
            >
              {label}
            </Link>
          ))}

          {/* Mobile theme toggle */}
          <div className="flex items-center justify-between px-3 py-2.5">
            <span className="text-sm font-medium text-[var(--text-secondary)]">Theme</span>
            <ThemeToggle theme={theme} onToggle={onToggleTheme} />
          </div>

          {/* Mobile user section */}
          {user && (
            <div className="pt-4 mt-3 border-t flex justify-center" style={{ borderColor: 'var(--border)' }}>
              <UserButton afterSignOutUrl="/" appearance={{ elements: { userButtonAvatarBox: "w-10 h-10 ring-2 ring-[var(--border)]" } }} />
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}