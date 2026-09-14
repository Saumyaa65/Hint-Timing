import React, { useState, useEffect, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { SignedIn, SignedOut, SignIn, useUser, useAuth } from '@clerk/clerk-react'
import TopicsHome from './pages/TopicsHome'
import TopicProblems from './pages/TopicProblems'
import ProblemList from './pages/ProblemList'
import ProblemDetail from './pages/ProblemDetail'
import AdminDashboard from './pages/AdminDashboard'
import UserAnalyticsDashboard from './pages/UserAnalyticsDashboard'
import ProblemSheets from './pages/ProblemSheets'
import SheetDetail from './pages/SheetDetail'
import Leaderboard from './pages/Leaderboard'
import Forum from './pages/Forum'
import Solutions from './pages/Solutions'
import Navbar from './components/Navbar'
import { setAuthToken } from './services/apiClient'

export default function App() {
  const { user, isLoaded } = useUser()
  const { getToken, signOut } = useAuth()

  useEffect(() => {
    const fetchToken = async () => {
      try {
        const token = await getToken()
        setAuthToken(token)
      } catch (err) {
        console.error("Failed to get token", err)
      }
    }
    fetchToken()
  }, [getToken])

  /* ── Theme: persisted in localStorage, applied to <html> ── */
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('hintcode-theme')
    return saved || 'dark'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('hintcode-theme', theme)
  }, [theme])

  const toggleTheme = useCallback(() => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  }, [])

  const handleSignOut = () => {
    signOut()
  }

  return (
    <BrowserRouter>
      <div className="h-screen bg-[var(--bg-base)] text-[var(--text-primary)] flex flex-col font-sans antialiased transition-colors duration-300 overflow-hidden">
        <SignedIn>
          <Navbar user={user} onSignOut={handleSignOut} theme={theme} onToggleTheme={toggleTheme} />
          <main className="flex-1 flex flex-col overflow-hidden min-h-0">
            <Routes>
              <Route path="/" element={<TopicsHome />} />
              <Route path="/topics/:topicName" element={<TopicProblems />} />
              <Route path="/problems" element={<ProblemList />} />
              <Route path="/problems/:id" element={<ProblemDetail user={user} theme={theme} />} />
              <Route path="/sheets" element={<ProblemSheets />} />
              <Route path="/sheets/:id" element={<SheetDetail />} />
              <Route path="/leaderboard" element={<Leaderboard />} />
              <Route path="/forum" element={<Forum />} />
              <Route path="/solutions/:problemId" element={<Solutions />} />
              <Route path="/analytics/me" element={<UserAnalyticsDashboard />} />
              <Route path="/admin/analytics" element={<AdminDashboard />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </SignedIn>
        <SignedOut>
          <div className="flex-1 flex items-center justify-center p-6 relative overflow-hidden">
            {/* Ambient glow orbs */}
            <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-indigo-500/8 rounded-full blur-[120px] -z-10 pointer-events-none animate-pulse"></div>
            <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-purple-600/8 rounded-full blur-[100px] -z-10 pointer-events-none animate-pulse" style={{ animationDelay: '1s' }}></div>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-500/5 rounded-full blur-[150px] -z-10 pointer-events-none"></div>
            <SignIn appearance={{ elements: { rootBox: "mx-auto" } }} />
          </div>
        </SignedOut>
      </div>
    </BrowserRouter>
  )
}
