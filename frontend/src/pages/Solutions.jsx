import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import apiClient from '../services/apiClient';

/* ─── relative time helper ─── */
function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

/* ─── skeleton card ─── */
function SkeletonCard() {
  return (
    <div className="rounded-2xl p-6 space-y-4 animate-pulse" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full" style={{ background: 'var(--bg-surface)' }} />
        <div className="h-3 w-28 rounded" style={{ background: 'var(--bg-surface)' }} />
      </div>
      <div className="h-4 w-3/4 rounded" style={{ background: 'var(--bg-surface)' }} />
      <div className="h-3 w-full rounded" style={{ background: 'var(--bg-surface)' }} />
      <div className="h-3 w-5/6 rounded" style={{ background: 'var(--bg-surface)' }} />
    </div>
  );
}

export default function Solutions() {
  const { problemId } = useParams();
  const navigate = useNavigate();

  const [solutions, setSolutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sort, setSort] = useState('upvotes'); // 'upvotes' | 'newest'
  const [expanded, setExpanded] = useState({}); // { [id]: bool }
  const [upvoted, setUpvoted] = useState({});   // { [id]: bool }

  useEffect(() => { fetchSolutions(); }, [problemId]);

  const fetchSolutions = async () => {
    try {
      setLoading(true);
      setError(null);
      const url = problemId ? `/solutions/?problem_id=${problemId}` : '/solutions/';
      const data = await apiClient.get(url);
      setSolutions(Array.isArray(data) ? data : (data.results || []));
    } catch (err) {
      console.error('Failed to load solutions', err);
      setError('Failed to load solutions.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpvote = async (id) => {
    if (upvoted[id]) return;
    try {
      await apiClient.post(`/solutions/${id}/upvote/`);
      setUpvoted(prev => ({ ...prev, [id]: true }));
      setSolutions(prev => prev.map(s => s.id === id ? { ...s, upvotes: (s.upvotes || 0) + 1 } : s));
    } catch (e) {
      // silently ignore if endpoint doesn't exist yet
    }
  };

  const toggleExpand = (id) => setExpanded(prev => ({ ...prev, [id]: !prev[id] }));

  const sorted = [...solutions].sort((a, b) => {
    if (sort === 'upvotes') return (b.upvotes || 0) - (a.upvotes || 0);
    return new Date(b.created_at) - new Date(a.created_at);
  });

  const LANG_BADGE = {
    javascript: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    python:     'bg-blue-500/10   text-blue-400   border-blue-500/20',
    java:       'bg-orange-500/10 text-orange-400  border-orange-500/20',
    cpp:        'bg-cyan-500/10   text-cyan-400    border-cyan-500/20',
    typescript: 'bg-indigo-500/10 text-indigo-400  border-indigo-500/20',
  };
  const langClass = (lang) => LANG_BADGE[lang] || 'bg-slate-700/40 text-slate-400 border-slate-600/30';

  return (
    <div className="flex-1 overflow-y-auto pb-20" style={{ background: 'var(--bg-base)' }}>
      {/* Ambient glow */}
      <div className="fixed top-24 left-1/3 w-[500px] h-[300px] bg-violet-500/[0.04] rounded-full blur-[150px] pointer-events-none -z-10" />

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8 animate-fade-in-up">

        {/* ── Header ── */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider mb-4 transition-colors hover:text-indigo-400"
              style={{ color: 'var(--text-secondary)' }}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back
            </button>
            <div className="inline-flex items-center gap-2 px-3 py-1 mb-3 rounded-full text-[10px] font-bold bg-violet-500/10 border border-violet-500/25 text-violet-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
              Community
            </div>
            <h1 className="text-3xl md:text-4xl font-black bg-gradient-to-r from-violet-400 via-indigo-400 to-blue-400 bg-clip-text text-transparent">
              Community Solutions
            </h1>
            <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
              Learn different approaches from the community
            </p>
          </div>

          {/* Sort selector */}
          {solutions.length > 0 && (
            <div className="flex items-center gap-1 rounded-xl p-1" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
              {[
                { key: 'upvotes', label: '🏅 Top' },
                { key: 'newest', label: '🕐 Latest' },
              ].map(opt => (
                <button
                  key={opt.key}
                  onClick={() => setSort(opt.key)}
                  className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${sort === opt.key ? 'bg-indigo-600 text-white' : 'hover:bg-[var(--bg-surface)] text-[var(--text-secondary)]'}`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* ── States ── */}
        {loading && (
          <div className="space-y-4">
            {[0, 1, 2].map(i => <SkeletonCard key={i} />)}
          </div>
        )}

        {!loading && error && (
          <div className="text-center py-16 space-y-3">
            <svg className="w-12 h-12 text-rose-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{error}</p>
            <button onClick={fetchSolutions} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg transition-colors">
              Retry
            </button>
          </div>
        )}

        {!loading && !error && sorted.length === 0 && (
          <div className="text-center py-20 rounded-2xl border border-dashed" style={{ borderColor: 'var(--border)' }}>
            <svg className="w-14 h-14 mx-auto mb-4 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: 'var(--text-muted)' }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-base font-bold" style={{ color: 'var(--text-primary)' }}>No solutions shared yet</p>
            <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Be the first to share your approach!</p>
          </div>
        )}

        {/* ── Solutions list ── */}
        {!loading && !error && sorted.length > 0 && (
          <div className="space-y-5">
            {sorted.map((sol, idx) => {
              const lang = sol.attempt?.language || 'code';
              const code = sol.attempt?.code || '';
              const isExpanded = expanded[sol.id];

              return (
                <div
                  key={sol.id || idx}
                  className="rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-xl"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    boxShadow: '0 2px 20px rgba(0,0,0,0.08)',
                  }}
                >
                  {/* Card header */}
                  <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: 'var(--border)' }}>
                    <div className="flex items-center gap-3">
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-black text-white flex-shrink-0"
                        style={{ background: `hsl(${(sol.username?.charCodeAt(0) || 0) * 15}, 65%, 50%)` }}
                      >
                        {(sol.username || 'A').charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
                          {sol.username || 'Anonymous'}
                        </span>
                        <span className="text-xs ml-2" style={{ color: 'var(--text-muted)' }}>
                          {timeAgo(sol.created_at)}
                        </span>
                      </div>
                    </div>
                    <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border uppercase ${langClass(lang)}`}>
                      {lang}
                    </span>
                  </div>

                  {/* Card body */}
                  <div className="px-6 py-5 space-y-4">
                    <h3 className="text-base font-bold" style={{ color: 'var(--text-primary)' }}>{sol.title}</h3>

                    {sol.explanation && (
                      <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                        {sol.explanation}
                      </p>
                    )}

                    {code && (
                      <div className="rounded-xl overflow-hidden" style={{ border: '1px solid var(--border)' }}>
                        <div
                          className="flex items-center justify-between px-4 py-2"
                          style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--border)' }}
                        >
                          <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
                            {lang}
                          </span>
                          <button
                            onClick={() => toggleExpand(sol.id)}
                            className="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
                          >
                            {isExpanded ? 'Collapse ↑' : 'Expand ↓'}
                          </button>
                        </div>
                        <pre
                          className="p-4 text-[11px] font-mono leading-relaxed overflow-x-auto transition-all duration-300"
                          style={{
                            background: '#0d1117',
                            color: '#c9d1d9',
                            maxHeight: isExpanded ? '600px' : '160px',
                          }}
                        >
                          {code}
                        </pre>
                      </div>
                    )}
                  </div>

                  {/* Card footer */}
                  <div className="flex items-center justify-between px-6 py-3 border-t" style={{ borderColor: 'var(--border)', background: 'var(--bg-surface)' }}>
                    <button
                      onClick={() => handleUpvote(sol.id)}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all active:scale-95 ${
                        upvoted[sol.id]
                          ? 'bg-indigo-600 text-white'
                          : 'hover:bg-indigo-500/10 hover:text-indigo-400'
                      }`}
                      style={{ color: upvoted[sol.id] ? undefined : 'var(--text-secondary)' }}
                    >
                      <svg className="w-4 h-4" fill={upvoted[sol.id] ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                      </svg>
                      {sol.upvotes || 0} Upvotes
                    </button>
                    <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                      Solution #{idx + 1}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
