import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../services/apiClient';

export default function ProblemSheets() {
  const [sheets, setSheets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSheets = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get('/sheets/');
        setSheets(Array.isArray(response) ? response : (response.results || []));
      } catch (err) {
        console.error('Error fetching sheets:', err);
        setError('Failed to load problem sheets.');
      } finally {
        setLoading(false);
      }
    };
    fetchSheets();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 overflow-y-auto bg-[var(--bg-base)] p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12 space-y-4">
            <div className="h-12 w-64 bg-[var(--bg-surface)] rounded-2xl mx-auto animate-pulse" />
            <div className="h-4 w-96 bg-[var(--bg-surface)] rounded-lg mx-auto animate-pulse" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-56 bg-[var(--bg-surface)] rounded-3xl border border-[var(--border)] animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 overflow-y-auto bg-[var(--bg-base)] flex items-center justify-center">
        <div className="text-center space-y-3">
          <svg className="w-12 h-12 text-red-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-[var(--text-secondary)] text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-[var(--bg-base)] relative pb-20">
      <div className="absolute top-0 left-1/4 w-[600px] h-[300px] bg-indigo-500/[0.04] rounded-full blur-[150px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 animate-fade-in-up">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 mb-4 rounded-full text-[10px] font-bold bg-indigo-500/10 border border-indigo-500/25 text-indigo-400 uppercase tracking-widest">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            Curated Collections
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-500 mb-4">
            Problem Sheets
          </h1>
          <p className="text-lg text-[var(--text-secondary)]">
            Curated lists of problems to help you master specific topics or prepare for interviews.
          </p>
        </div>

        {sheets.length === 0 ? (
          <div className="text-center py-20 border border-dashed border-[var(--border)] rounded-3xl">
            <svg className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-4 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <p className="text-[var(--text-secondary)] text-sm font-semibold">No sheets available yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {sheets.map((sheet) => (
              <Link
                key={sheet.id}
                to={`/sheets/${sheet.id}`}
                className="group relative block p-8 rounded-3xl bg-[var(--card-bg)] border border-[var(--border)] overflow-hidden transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:shadow-indigo-500/20 hover:border-indigo-500/40"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-violet-600/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                <div className="relative z-10 flex flex-col h-full">
                  <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-indigo-500/20 transition-all duration-300">
                    <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </div>

                  <h3 className="text-2xl font-bold mb-3 text-[var(--text-primary)] group-hover:text-indigo-400 transition-colors">
                    {sheet.title}
                  </h3>

                  <p className="text-[var(--text-secondary)] text-sm flex-grow mb-6 leading-relaxed">
                    {sheet.description || 'A curated collection of problems to challenge your skills.'}
                  </p>

                  <div className="flex items-center justify-between text-sm font-medium">
                    <span className="bg-[var(--bg-surface)] border border-[var(--border)] text-[var(--text-secondary)] px-3 py-1 rounded-full text-xs font-bold">
                      {sheet.sheet_problems?.length || 0} Problems
                    </span>
                    <span className="text-indigo-400 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300 flex items-center gap-1 text-xs font-bold">
                      Solve now
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                      </svg>
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
