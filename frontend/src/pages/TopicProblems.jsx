import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import problemService from '../services/problemService';

// Custom Minimalist SVG Icons for topics
const TopicIcon = ({ topic }) => {
  const normalized = topic?.toLowerCase() || '';
  
  if (normalized.includes('array')) {
    return (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <rect x={3} y={3} width={7} height={7} rx={1.5} />
        <rect x={14} y={3} width={7} height={7} rx={1.5} />
        <rect x={3} y={14} width={7} height={7} rx={1.5} />
        <rect x={14} y={14} width={7} height={7} rx={1.5} />
      </svg>
    );
  }
  if (normalized.includes('string')) {
    return (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 5h12M3 10h18M3 15h14M3 20h10" />
      </svg>
    );
  }
  if (normalized.includes('tree') || normalized.includes('trie')) {
    return (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v18M12 7l-4 4m4-4l4 4M12 13l-6 6m6-6l6 6" />
      </svg>
    );
  }
  if (normalized.includes('graph')) {
    return (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <circle cx={12} cy={5} r={3} />
        <circle cx={5} cy={18} r={3} />
        <circle cx={19} cy={18} r={3} />
        <path d="M10 7.5L6.5 15.5M14 7.5l3.5 15.5M8 18h8" />
      </svg>
    );
  }
  if (normalized.includes('dynamic') || normalized.includes('dp')) {
    return (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    );
  }
  if (normalized.includes('greedy') || normalized.includes('sort')) {
    return (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 4h13M3 8h9M3 12h5m0 0v8m0-8l-4 4m4-4l4 4M21 12v8m0-8l-3 3m3-3l3 3" />
      </svg>
    );
  }
  if (normalized.includes('search') || normalized.includes('find')) {
    return (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <circle cx={11} cy={11} r={8} />
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35" />
      </svg>
    );
  }
  if (normalized.includes('list')) {
    return (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
      </svg>
    );
  }
  if (normalized.includes('stack') || normalized.includes('queue')) {
    return (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    );
  }
  return (
    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  );
};

export default function TopicProblems() {
  const { topicName } = useParams();
  const navigate = useNavigate();
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDifficulty, setSelectedDifficulty] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [solvedList, setSolvedList] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState('');
  const [sortDirection, setSortDirection] = useState('asc');
  const itemsPerPage = 25;
  const decodedTopic = decodeURIComponent(topicName);

  useEffect(() => {
    loadProblems();
    loadSolvedList();
  }, [topicName]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedDifficulty, selectedStatus, sortField, sortDirection]);

  const loadSolvedList = () => {
    try {
      const stored = JSON.parse(localStorage.getItem('solvedProblems') || '[]');
      setSolvedList(stored);
    } catch (e) {
      console.error(e);
    }
  };

  const loadProblems = async () => {
    try {
      setLoading(true);
      const data = await problemService.getAllProblems();
      const topicProblems = data.filter(p => p.topic === decodedTopic);
      setProblems(topicProblems);
    } catch (error) {
      console.error('Error loading problems:', error);
    } finally {
      setLoading(false);
    }
  };

  const isSolved = (problem) => {
    return solvedList.includes(problem.problem_id) || solvedList.includes(problem.id?.toString());
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case 'easy': return 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/25 px-2.5 py-0.5 rounded-full font-bold';
      case 'medium': return 'text-amber-400 bg-amber-500/10 border border-amber-500/25 px-2.5 py-0.5 rounded-full font-bold';
      case 'hard': return 'text-red-400 bg-red-500/10 border border-red-500/25 px-2.5 py-0.5 rounded-full font-bold';
      default: return 'text-slate-500';
    }
  };

  const capitalizeFirst = (str) => {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  const filteredProblems = problems.filter(problem => {
    const matchesSearch = problem.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          problem.problem_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDifficulty = !selectedDifficulty || problem.difficulty?.toLowerCase() === selectedDifficulty;
    
    const solved = isSolved(problem);
    const matchesStatus = !selectedStatus || 
      (selectedStatus === 'solved' && solved) || 
      (selectedStatus === 'unsolved' && !solved);

    return matchesSearch && matchesDifficulty && matchesStatus;
  });

  const sortedProblems = [...filteredProblems].sort((a, b) => {
    if (!sortField) return 0;
    
    let aVal, bVal;
    if (sortField === 'title') {
      aVal = a.title.toLowerCase();
      bVal = b.title.toLowerCase();
    } else if (sortField === 'difficulty') {
      const diffWeight = { easy: 1, medium: 2, hard: 3 };
      aVal = diffWeight[a.difficulty.toLowerCase()] || 0;
      bVal = diffWeight[b.difficulty.toLowerCase()] || 0;
    } else if (sortField === 'acceptance_rate') {
      aVal = a.acceptance_rate ? a.acceptance_rate * 100 : (45 + (a.title.charCodeAt(0) % 35));
      bVal = b.acceptance_rate ? b.acceptance_rate * 100 : (45 + (b.title.charCodeAt(0) % 35));
    } else {
      return 0;
    }
    
    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  // Pagination bounds
  const totalPages = Math.ceil(sortedProblems.length / itemsPerPage);
  const currentProblems = sortedProblems.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const renderSortIndicator = (field) => {
    if (sortField !== field) {
      return (
        <svg className="w-3 h-3 text-slate-600 inline ml-1 opacity-0 group-hover/header:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      );
    }
    return sortDirection === 'asc' ? (
      <svg className="w-3 h-3 text-indigo-400 inline ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
      </svg>
    ) : (
      <svg className="w-3 h-3 text-indigo-400 inline ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
      </svg>
    );
  };

  const easyCount = problems.filter(p => p.difficulty?.toLowerCase() === 'easy').length;
  const mediumCount = problems.filter(p => p.difficulty?.toLowerCase() === 'medium').length;
  const hardCount = problems.filter(p => p.difficulty?.toLowerCase() === 'hard').length;

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[var(--bg-base)]">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-500 mx-auto"></div>
          <p className="text-[#8b949e] text-xs font-semibold tracking-widest uppercase">Loading catalog...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto bg-[var(--bg-base)] pb-16 relative">
      <div className="bg-grid-overlay" />
      <div className="bg-dot-overlay" />

      {/* Header Panel */}
      <div className="border-b border-[var(--border)] bg-[var(--bg-surface)]/30 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <button
            onClick={() => navigate('/')}
            className="inline-flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 hover:text-indigo-400 mb-6 group transition-colors focus:outline-none"
          >
            <svg className="w-4 h-4 transform group-hover:-translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </button>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-[var(--bg-surface)]/80 border border-[var(--border)] rounded-2xl flex items-center justify-center text-indigo-400 shadow-inner">
                <TopicIcon topic={decodedTopic} />
              </div>
              <div>
                <h1 className="text-3xl font-black text-white tracking-tight">
                  {decodedTopic}
                </h1>
                <p className="text-[#8b949e] text-xs font-bold uppercase tracking-wider mt-1">
                  {problems.length} Challenges Loaded
                </p>
              </div>
            </div>

            {/* Quick Metrics */}
            <div className="flex flex-row items-center gap-4 bg-[var(--bg-surface)]/50 border border-[var(--border)] p-3.5 rounded-2xl shadow-sm">
              <div className="text-center px-4 border-r border-[var(--border)]">
                <span className="text-base font-black text-emerald-400 block">{easyCount}</span>
                <span className="text-[10px] text-slate-500 font-bold block uppercase tracking-wider">Easy</span>
              </div>
              <div className="text-center px-4 border-r border-[var(--border)]">
                <span className="text-base font-black text-amber-400 block">{mediumCount}</span>
                <span className="text-[10px] text-slate-500 font-bold block uppercase tracking-wider">Medium</span>
              </div>
              <div className="text-center px-4">
                <span className="text-base font-black text-red-400 block">{hardCount}</span>
                <span className="text-[10px] text-slate-500 font-bold block uppercase tracking-wider">Hard</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-4 w-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </span>
            <input
              type="text"
              placeholder="Search topic challenges..."
              className="w-full pl-10 pr-4 py-2.5 bg-[var(--bg-surface)]/60 border border-[var(--border)] rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-all text-xs"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <select
            aria-label="Filter by difficulty"
            className="w-full px-4 py-2.5 bg-[var(--bg-surface)]/60 border border-[var(--border)] rounded-xl text-slate-400 focus:outline-none focus:border-indigo-500/50 transition-all text-xs cursor-pointer"
            value={selectedDifficulty}
            onChange={(e) => setSelectedDifficulty(e.target.value)}
          >
            <option value="">All Difficulties</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>

          <select
            aria-label="Filter by status"
            className="w-full px-4 py-2.5 bg-[var(--bg-surface)]/60 border border-[var(--border)] rounded-xl text-slate-400 focus:outline-none focus:border-indigo-500/50 transition-all text-xs cursor-pointer"
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="solved">Solved</option>
            <option value="unsolved">Unsolved</option>
          </select>
        </div>

        {/* Problems List Table */}
        <div className="bg-[var(--bg-surface)]/30 border border-[var(--border)] rounded-2xl overflow-hidden shadow-2xl backdrop-blur-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[var(--border)] select-none bg-[var(--bg-surface)]/60">
                  <th className="py-4 pl-6 pr-2 w-12 text-xs uppercase tracking-wider text-slate-500 font-medium">#</th>
                  <th className="py-4 px-3 w-14 text-center text-xs uppercase tracking-wider text-slate-500 font-medium">Status</th>
                  <th 
                    onClick={() => handleSort('title')}
                    className="py-4 px-4 min-w-[200px] cursor-pointer hover:bg-slate-800/40 transition-colors group/header text-xs uppercase tracking-wider text-slate-500 font-medium"
                  >
                    Title {renderSortIndicator('title')}
                  </th>
                  <th 
                    onClick={() => handleSort('difficulty')}
                    className="py-4 px-4 w-32 cursor-pointer hover:bg-slate-800/40 transition-colors group/header text-xs uppercase tracking-wider text-slate-500 font-medium"
                  >
                    Difficulty {renderSortIndicator('difficulty')}
                  </th>
                  <th 
                    onClick={() => handleSort('acceptance_rate')}
                    className="py-4 px-6 w-28 text-right cursor-pointer hover:bg-slate-800/40 transition-colors group/header text-xs uppercase tracking-wider text-slate-500 font-medium"
                  >
                    Acceptance {renderSortIndicator('acceptance_rate')}
                  </th>
                </tr>
              </thead>
              <tbody className="font-medium">
                {currentProblems.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-16 text-center text-slate-500 font-bold uppercase tracking-widest text-[10px]">
                      No topic challenges match your search filters.
                    </td>
                  </tr>
                ) : (
                  currentProblems.map((problem, index) => {
                    const solved = isSolved(problem);
                    const rowNum = (currentPage - 1) * itemsPerPage + index + 1;
                    return (
                      <tr 
                        key={problem.id}
                        role="button"
                        onClick={() => navigate(`/problems/${problem.id}`)}
                        className={`border-l-2 border-l-transparent hover:border-l-indigo-500 cursor-pointer transition-all duration-200 group ${
                          index % 2 === 0 ? 'bg-transparent' : 'bg-white/[0.01]'
                        } hover:bg-white/[0.03]`}
                      >
                        {/* Row Number */}
                        <td className="py-3.5 pl-6 pr-2 text-xs text-slate-600 font-mono tabular-nums">
                          {rowNum}
                        </td>

                        {/* Status Checkmark */}
                        <td className="py-3.5 px-3 text-center">
                          {solved ? (
                            <div className="w-5 h-5 rounded-full bg-green-500/10 border border-green-500/30 flex items-center justify-center text-green-400 mx-auto shadow-sm shadow-green-500/5">
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={3} viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                              </svg>
                            </div>
                          ) : (
                            <div className="w-4 h-4 rounded-full border border-slate-700/60 mx-auto group-hover:border-slate-500 transition-colors" />
                          )}
                        </td>

                        {/* Title link */}
                        <td className="py-3.5 px-4 text-sm font-medium text-slate-200 group-hover:text-indigo-400 transition-colors">
                          {problem.title}
                        </td>

                        {/* Difficulty label */}
                        <td className="py-3.5 px-4">
                          <span className={getDifficultyColor(problem.difficulty)}>
                            {capitalizeFirst(problem.difficulty)}
                          </span>
                        </td>

                        {/* Acceptance rate */}
                        <td className="py-3.5 px-6 text-right text-slate-400 font-bold">
                          {problem.acceptance_rate 
                            ? `${Math.round(problem.acceptance_rate * 100)}%` 
                            : `${45 + (problem.title.charCodeAt(0) % 35)}%`
                          }
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-6">
            <span className="text-xs text-[#8b949e] font-bold">
              Showing page {currentPage} of {totalPages}
            </span>

            <div className="flex items-center gap-1.5 bg-[var(--bg-surface)] p-1.5 border border-[var(--border)] rounded-xl shadow-xl select-none">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="p-2 rounded-lg text-slate-400 hover:text-slate-100 disabled:opacity-30 disabled:hover:text-slate-400 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              
              {Array.from({ length: Math.min(5, totalPages) }, (_, idx) => {
                let pageNum = currentPage - 2 + idx;
                if (currentPage <= 2) pageNum = idx + 1;
                else if (currentPage >= totalPages - 1) pageNum = totalPages - 4 + idx;
                
                if (pageNum <= 0 || pageNum > totalPages) return null;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`w-8 h-8 rounded-lg text-xs font-black transition-all ${
                      currentPage === pageNum
                        ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/40 shadow'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}

              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="p-2 rounded-lg text-slate-400 hover:text-slate-100 disabled:opacity-30 disabled:hover:text-slate-400 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
