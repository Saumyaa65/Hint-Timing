import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import apiClient from '../services/apiClient';

export default function SheetDetail() {
  const { id } = useParams();
  const [sheet, setSheet] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSheet = async () => {
      try {
        const response = await apiClient.get(`/sheets/${id}/`);
        setSheet(response);
      } catch (error) {
        console.error('Error fetching sheet:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchSheet();
  }, [id]);

  if (loading) {
    return (
      <div className="flex-1 flex justify-center items-center bg-[var(--bg-base)]">
        <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (!sheet) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[var(--bg-base)]">
        <p className="text-[var(--text-secondary)] text-sm">Sheet not found or failed to load.</p>
      </div>
    );
  }

  const problems = sheet.sheet_problems || [];
  
  // Note: Solved status requires fetching user history, or adding it to the serializer.
  // For the MVP, we just list the problems.

  return (
    <div className="flex-1 overflow-y-auto bg-[var(--bg-base)]">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 animate-fade-in-up">
      <div className="mb-10">
        <Link to="/sheets" className="inline-flex items-center text-sm font-medium text-indigo-500 hover:text-indigo-400 mb-6 transition-colors">
          <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Sheets
        </Link>
        <h1 className="text-4xl font-extrabold mb-4">{sheet.title}</h1>
        <p className="text-lg text-[var(--text-secondary)] mb-8">
          {sheet.description}
        </p>
      </div>

      <div className="bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl overflow-hidden shadow-sm">
        <ul className="divide-y divide-[var(--border)]">
          {problems.map((sp, index) => (
            <li key={sp.id} className="hover:bg-[var(--bg-elevated)] transition-colors">
              <Link to={`/problems/${sp.problem.id}`} className="block p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-8 flex justify-center text-lg font-bold text-[var(--text-secondary)]">
                      {index + 1}
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold mb-1 group-hover:text-indigo-500">
                        {sp.problem.title}
                      </h3>
                      <div className="flex items-center gap-3 text-sm">
                        <span className={`px-2.5 py-0.5 rounded-full font-medium ${
                          sp.problem.difficulty === 'easy' ? 'bg-emerald-500/10 text-emerald-500' :
                          sp.problem.difficulty === 'medium' ? 'bg-amber-500/10 text-amber-500' :
                          'bg-rose-500/10 text-rose-500'
                        }`}>
                          {sp.problem.difficulty.charAt(0).toUpperCase() + sp.problem.difficulty.slice(1)}
                        </span>
                        <span className="text-[var(--text-secondary)]">
                          {sp.problem.topic || 'General'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-indigo-500 font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    Solve
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
        {problems.length === 0 && (
          <div className="p-10 text-center text-[var(--text-secondary)]">
            No problems added to this sheet yet.
          </div>
        )}
      </div>
      </div>
    </div>
  );
}
