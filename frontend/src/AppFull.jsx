import React, {useState, useEffect} from 'react'
import { BrowserRouter } from 'react-router-dom'
import ProblemList from './pages/ProblemList'
import ProblemDetail from './pages/ProblemDetail'
import SignIn from './components/SignIn'
import Navbar from './components/Navbar'
import './styles/globals.css'

export default function AppFull(){
  const [user, setUser] = useState(null)
  const [selectedView, setSelectedView] = useState('problems') // 'problems' or 'detail'
  
  useEffect(() => {
    const u = localStorage.getItem('user')
    if(u) setUser(JSON.parse(u))
    
    // Listen for problem open events to switch view
    const handleOpenProblem = () => {
      setSelectedView('detail')
    }
    
    window.addEventListener('openProblem', handleOpenProblem)
    return () => window.removeEventListener('openProblem', handleOpenProblem)
  }, [])

  function handleSignIn(u) {
    setUser(u)
  }
  
  function handleSignOut() {
    localStorage.removeItem('user')
    setUser(null)
  }

  // If not signed in, show sign-in screen
  if (!user) {
    return (
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50 flex flex-col">
          <Navbar />
          <div className="flex-1 flex justify-center items-center p-10">
            <SignIn onSignIn={handleSignIn} />
          </div>
        </div>
      </BrowserRouter>
    )
  }

  // Mobile view switcher (for responsive design)
  function renderMobileNavigation() {
    return (
      <div className="flex border-b border-gray-200 mb-3 px-3 bg-white">
        <button 
          onClick={() => setSelectedView('problems')}
          className={`px-4 py-3 flex-1 text-center font-medium border-b-2 transition-colors ${
            selectedView === 'problems' 
              ? 'text-blue-600 border-blue-600 bg-gray-50' 
              : 'text-gray-500 border-transparent hover:text-gray-700'
          }`}
        >
          Problems
        </button>
        <button 
          onClick={() => setSelectedView('detail')}
          className={`px-4 py-3 flex-1 text-center font-medium border-b-2 transition-colors ${
            selectedView === 'detail' 
              ? 'text-blue-600 border-blue-600 bg-gray-50' 
              : 'text-gray-500 border-transparent hover:text-gray-700'
          }`}
        >
          Code Editor
        </button>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <div className="flex flex-col h-screen bg-gray-50">
        <Navbar user={user} onSignOut={handleSignOut} />
        
      {/* Mobile navigation (visible only on small screens) */}
      <div className="block md:hidden">
        {renderMobileNavigation()}
      </div>        <main className="flex flex-col md:flex-row gap-0 md:gap-5 p-0 md:p-5 flex-1 overflow-hidden">
          {/* Problem list sidebar (hidden on mobile when detail view is selected) */}
          <div className={`flex-none w-full md:w-80 bg-white md:rounded-lg md:shadow-sm overflow-auto ${
            selectedView === 'problems' ? 'block' : 'hidden md:block'
          }`}>
            <ProblemList onOpen={(p) => {
              window.__openProblem = p;
              // Ensure the event is dispatched after setting the global variable
              setTimeout(() => {
                window.dispatchEvent(new CustomEvent('openProblem', { detail: p }));
              }, 0);
            }} />
          </div>
          
          {/* Problem detail and code editor */}
          <div className={`flex-1 bg-white md:rounded-lg md:shadow-sm overflow-hidden ${
            selectedView === 'detail' ? 'block' : 'hidden md:block'
          }`}>
            <ProblemDetail user={user} />
          </div>
        </main>


      </div>
    </BrowserRouter>
  )
}
