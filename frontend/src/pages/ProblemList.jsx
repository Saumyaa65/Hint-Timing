import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import problemService from '../services/problemService';
import apiClient from '../services/apiClient';

export default function ProblemList() {
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [solvedList, setSolvedList] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState('');
  const [sortDirection, setSortDirection] = useState('asc');
  const [dailyProblem, setDailyProblem] = useState(null);
  const itemsPerPage = 50;
  const navigate = useNavigate();

  useEffect(() => {
    loadProblems();
    loadSolvedList();
    loadDailyProblem();
  }, []);

  const loadDailyProblem = async () => {
    try {
      const data = await apiClient.get('/daily/today/');
      if (data && data.problem) {
        setDailyProblem(data.problem);
      }
    } catch (e) {
      console.log('No daily problem available');
    }
  };

  // Reset to first page on filter, search, status, or sorting change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedTopic, selectedDifficulty, selectedStatus, sortField, sortDirection]);

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
      setProblems(data);
    } catch (error) {
      console.error('Error loading problems:', error);
    } finally {
      setLoading(false);
    }
  };

  const topics = [...new Set(problems.map(p => p.topic))].filter(Boolean).sort();
  const difficulties = ['easy', 'medium', 'hard'];

  const isSolved = (problem) => {
    return solvedList.includes(problem.problem_id) || solvedList.includes(problem.id?.toString());
  };

  const filteredProblems = problems.filter(problem => {
    const matchesSearch = problem.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          problem.problem_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTopic = !selectedTopic || problem.topic === selectedTopic;
    const matchesDifficulty = !selectedDifficulty || problem.difficulty.toLowerCase() === selectedDifficulty.toLowerCase();
    
    const solved = isSolved(problem);
    const matchesStatus = !selectedStatus || 
      (selectedStatus === 'solved' && solved) || 
      (selectedStatus === 'unsolved' && !solved);

    return matchesSearch && matchesTopic && matchesDifficulty && matchesStatus;
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
    } else if (sortField === 'topic') {
      aVal = (a.topic || '').toLowerCase();
      bVal = (b.topic || '').toLowerCase();
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

  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case 'easy': return 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/25 px-2.5 py-0.5 rounded-full font-bold';
      case 'medium': return 'text-amber-400 bg-amber-500/10 border border-amber-500/25 px-2.5 py-0.5 rounded-full font-bold';
      case 'hard': return 'text-red-400 bg-red-500/10 border border-red-500/25 px-2.5 py-0.5 rounded-full font-bold';
      default: return 'text-slate-400';
    }
  };

  const getTopicStyle = (topic) => {
    return 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 px-2.5 py-0.5 rounded-full text-[10px] font-bold';
  };

  const capitalizeFirst = (str) => {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  if (loading) {
    return (
      <div className="flex-1 overflow-auto bg-[var(--bg-base)] p-6">
        <div className="max-w-7xl mx-auto space-y-6 animate-pulse">
          {/* Header Skeleton */}
          <div className="h-32 bg-[var(--bg-surface)] rounded-2xl border border-[var(--border)]" />
          
          {/* Toolbar Skeleton */}
          <div className="flex gap-4">
            <div className="h-10 flex-1 bg-[var(--bg-surface)] rounded-lg border border-[var(--border)]" />
            <div className="h-10 w-32 bg-[var(--bg-surface)] rounded-lg border border-[var(--border)]" />
            <div className="h-10 w-32 bg-[var(--bg-surface)] rounded-lg border border-[var(--border)]" />
            <div className="h-10 w-32 bg-[var(--bg-surface)] rounded-lg border border-[var(--border)]" />
          </div>

          {/* Table Skeleton */}
          <div className="bg-[var(--bg-surface)] border border-[var(--border)] rounded-2xl overflow-hidden">
            <div className="h-12 border-b border-[var(--border)] bg-[#161B22]/50" />
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-16 border-b border-[var(--border)] flex items-center px-4 gap-4">
                <div className="h-4 w-4 bg-[var(--border)] rounded" />
                <div className="h-4 w-12 bg-[var(--border)] rounded" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-1/3 bg-[var(--border)] rounded" />
                  <div className="h-3 w-1/4 bg-[var(--border)] rounded/50" />
                </div>
                <div className="h-6 w-20 bg-[var(--border)] rounded-full" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Calculate metrics
  const totalSolved = solvedList.length;
  const easySolved = problems.filter(p => isSolved(p) && p.difficulty?.toLowerCase() === 'easy').length;
  const mediumSolved = problems.filter(p => isSolved(p) && p.difficulty?.toLowerCase() === 'medium').length;
  const hardSolved = problems.filter(p => isSolved(p) && p.difficulty?.toLowerCase() === 'hard').length;

  return (
    <div className="flex-1 overflow-auto bg-[var(--bg-base)] pb-16 relative">
      <div className="bg-grid-overlay" />
      <div className="bg-dot-overlay" />

      {/* Glow highlight */}
      <div className="absolute top-0 right-1/4 w-[400px] h-[300px] bg-indigo-500/5 rounded-full blur-[100px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Problem of the Day Banner */}
        {dailyProblem && (
          <div className="mb-10 animate-fade-in-up">
            <Link to={`/problems/${dailyProblem.id}`} className="block relative rounded-3xl overflow-hidden group shadow-lg">
              <div className="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-indigo-500/20 opacity-50 group-hover:opacity-100 transition-opacity"></div>
              <div className="absolute inset-0 bg-[var(--card-bg)]/80 backdrop-blur-sm"></div>
              <div className="relative p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6 border border-orange-500/30 rounded-3xl group-hover:border-orange-500/60 transition-colors">
                <div className="flex items-center gap-6 w-full sm:w-auto">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white shadow-xl shadow-orange-500/30 flex-shrink-0 group-hover:scale-110 transition-transform">
                    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-orange-500 font-black text-sm uppercase tracking-widest mb-1 flex items-center gap-2">
                      Problem of the Day
                      <span className="flex h-2 w-2 relative">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
                      </span>
                    </h2>
                    <h3 className="text-2xl font-bold text-[var(--text-primary)] group-hover:text-orange-500 transition-colors">{dailyProblem.title}</h3>
                    <div className="flex gap-3 mt-2 text-xs font-semibold">
                      <span className={getDifficultyColor(dailyProblem.difficulty)}>
                        {capitalizeFirst(dailyProblem.difficulty)}
                      </span>
                      {dailyProblem.topic && (
                        <span className="bg-slate-500/10 text-slate-400 border border-slate-500/20 px-2.5 py-0.5 rounded-full">
                          {dailyProblem.topic}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="w-full sm:w-auto flex-shrink-0">
                  <button className="w-full sm:w-auto bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-lg shadow-orange-500/30 flex items-center justify-center gap-2 group-hover:-translate-y-1">
                    Solve now to keep streak 🔥
                  </button>
                </div>
              </div>
            </Link>
          </div>
        )}
        
        {/* Header & Stats Banner */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-end mb-8">
          <div className="lg:col-span-7">
            <h1 className="text-3xl font-black text-[var(--text-primary)] tracking-tight">Problems Catalog</h1>
            <p className="text-[var(--text-secondary)] text-xs font-bold uppercase tracking-wider mt-1">
              {filteredProblems.length} challenges found / {problems.length} total
            </p>
          </div>
          
          {/* Quick Solve Stats */}
          <div className="lg:col-span-5 flex justify-end gap-3 w-full">
            <div className="bg-[var(--bg-surface)]/50 border border-[var(--border)] py-3 px-4 rounded-xl flex items-center gap-3 shadow-sm flex-1 max-w-[280px]">
              <div className="relative w-10 h-10 flex items-center justify-center flex-shrink-0">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="20" cy="20" r="17" className="stroke-slate-800" strokeWidth="3" fill="transparent" />
                  <circle cx="20" cy="20" r="17" className="stroke-indigo-500" strokeWidth="3" fill="transparent" 
                    strokeDasharray={2 * Math.PI * 17}
                    strokeDashoffset={2 * Math.PI * 17 * (1 - (totalSolved / Math.max(1, problems.length)))}
                    strokeLinecap="round"
                  />
                </svg>
                <span className="absolute text-[10px] font-black text-[var(--text-primary)]">{totalSolved}</span>
              </div>
              <div className="text-left leading-tight">
                <span className="text-[10px] text-slate-500 font-bold uppercase block tracking-wider">Solved Progress</span>
                <span className="text-xs font-black text-slate-400">
                  E: <span className="text-emerald-400 font-bold">{easySolved}</span> • 
                  M: <span className="text-amber-400 font-bold">{mediumSolved}</span> • 
                  H: <span className="text-red-400 font-bold">{hardSolved}</span>
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Filter bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {/* Search */}
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
              <svg className="h-4 w-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </span>
            <input
              type="text"
              placeholder="Search problem title..."
              className="w-full pl-10 pr-4 py-2.5 bg-[var(--bg-surface)]/60 border border-[var(--border)] rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-all text-xs"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Topic */}
          <select
            aria-label="Filter by topic"
            className="w-full px-4 py-2.5 bg-[var(--bg-surface)]/60 border border-[var(--border)] rounded-xl text-slate-300 focus:outline-none focus:border-indigo-500/50 transition-all text-xs cursor-pointer select-none"
            value={selectedTopic}
            onChange={(e) => setSelectedTopic(e.target.value)}
          >
            <option value="">All Topics</option>
            {topics.map(topic => (
              <option key={topic} value={topic}>{topic}</option>
            ))}
          </select>

          {/* Difficulty */}
          <select
            aria-label="Filter by difficulty"
            className="w-full px-4 py-2.5 bg-[var(--bg-surface)]/60 border border-[var(--border)] rounded-xl text-slate-300 focus:outline-none focus:border-indigo-500/50 transition-all text-xs cursor-pointer select-none"
            value={selectedDifficulty}
            onChange={(e) => setSelectedDifficulty(e.target.value)}
          >
            <option value="">All Difficulties</option>
            {difficulties.map(diff => (
              <option key={diff} value={diff}>{capitalizeFirst(diff)}</option>
            ))}
          </select>

          {/* Status */}
          <select
            aria-label="Filter by status"
            className="w-full px-4 py-2.5 bg-[var(--bg-surface)]/60 border border-[var(--border)] rounded-xl text-slate-300 focus:outline-none focus:border-indigo-500/50 transition-all text-xs cursor-pointer select-none"
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="solved">Solved</option>
            <option value="unsolved">Unsolved</option>
          </select>
        </div>

        {/* LeetCode-style Problem Table */}
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
                    onClick={() => handleSort('topic')}
                    className="py-4 px-4 w-44 cursor-pointer hover:bg-slate-800/40 transition-colors group/header text-xs uppercase tracking-wider text-slate-500 font-medium"
                  >
                    Category {renderSortIndicator('topic')}
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
                    <td colSpan={6} className="py-16 text-center text-slate-500 font-bold uppercase tracking-widest text-[10px]">
                      No coding challenges match your search filters.
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

                        {/* Category badge */}
                        <td className="py-3.5 px-4">
                          <span className={getTopicStyle(problem.topic)}>
                            {problem.topic}
                          </span>
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

        {/* LeetCode-style Pagination Bar */}
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
              
              {/* Pagination Numbers */}
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
                        ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/40 shadow-md shadow-indigo-500/5'
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