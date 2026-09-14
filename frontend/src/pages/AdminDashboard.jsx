import React, { useState, useEffect } from 'react';
import apiClient from '../services/apiClient';

/* ─── tiny helpers ─── */
const DIFF_STYLES = {
  easy:   { text: 'text-emerald-400', bg: 'bg-emerald-500/10 border border-emerald-500/20' },
  medium: { text: 'text-amber-400',   bg: 'bg-amber-500/10   border border-amber-500/20' },
  hard:   { text: 'text-rose-400',    bg: 'bg-rose-500/10    border border-rose-500/20' },
};
const cap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : '';

function KpiCard({ icon, value, label, fromColor, toColor, glowColor }) {
  return (
    <div
      className="relative flex flex-col gap-3 rounded-2xl p-6 overflow-hidden"
      style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', boxShadow: `0 0 40px 0 ${glowColor}18` }}
    >
      <div
        className="absolute -top-6 -right-6 w-24 h-24 rounded-full blur-2xl pointer-events-none opacity-25"
        style={{ background: `linear-gradient(135deg, ${fromColor}, ${toColor})` }}
      />
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center text-white flex-shrink-0"
        style={{ background: `linear-gradient(135deg, ${fromColor}, ${toColor})` }}
      >
        {icon}
      </div>
      <div>
        <p className="text-3xl font-black" style={{ color: 'var(--text-primary)' }}>{value}</p>
        <p className="text-xs font-bold uppercase tracking-widest mt-1" style={{ color: 'var(--text-secondary)' }}>{label}</p>
      </div>
    </div>
  );
}

function RankBadge({ rank }) {
  if (rank === 1) return <span className="text-lg">🥇</span>;
  if (rank === 2) return <span className="text-lg">🥈</span>;
  if (rank === 3) return <span className="text-lg">🥉</span>;
  return <span className="text-xs font-bold" style={{ color: 'var(--text-secondary)' }}>#{rank}</span>;
}

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.get('/analytics/admin_dashboard/');
      setData(res);
    } catch (err) {
      console.error('Failed to load admin analytics', err);
      setError('Failed to load analytics. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center" style={{ background: 'var(--bg-base)' }}>
        <div className="text-center space-y-3">
          <div className="w-12 h-12 border-4 border-rose-500/30 border-t-rose-500 rounded-full animate-spin mx-auto" />
          <p className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--text-secondary)' }}>Loading analytics…</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex-1 flex items-center justify-center p-8" style={{ background: 'var(--bg-base)' }}>
        <div className="text-center space-y-4">
          <svg className="w-12 h-12 text-rose-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{error || 'No data available.'}</p>
          <button onClick={fetchData} className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg transition-colors">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const { total_users, total_problems, total_attempts, successful_attempts, global_solve_rate, popular_problems } = data;
  const maxAttempts = popular_problems?.length > 0 ? Math.max(...popular_problems.map(p => p.attempts || 0)) : 1;
  const avgAttemptsPerUser = total_users > 0 ? (total_attempts / total_users).toFixed(1) : '0';
  const problemsPerUser = total_users > 0 ? (total_problems / total_users).toFixed(1) : '0';

  return (
    <div className="flex-1 overflow-y-auto pb-20 animate-fade-in-up" style={{ background: 'var(--bg-base)' }}>
      {/* Ambient glow */}
      <div className="fixed top-20 right-1/4 w-[500px] h-[300px] bg-rose-500/[0.03] rounded-full blur-[150px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">

        {/* ── Header ── */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 mb-3 rounded-full text-[10px] font-bold bg-rose-500/10 border border-rose-500/25 text-rose-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
              Admin Panel
            </div>
            <h1 className="text-3xl md:text-4xl font-black bg-gradient-to-r from-rose-400 via-orange-400 to-amber-400 bg-clip-text text-transparent">
              Admin Dashboard
            </h1>
            <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
              Platform-wide analytics and insights
            </p>
          </div>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition-all hover:scale-105 active:scale-95"
            style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>

        {/* ── KPI Cards ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
          <KpiCard
            icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>}
            value={total_users.toLocaleString()}
            label="Total Users"
            fromColor="#6366f1" toColor="#8b5cf6" glowColor="#6366f1"
          />
          <KpiCard
            icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>}
            value={total_problems.toLocaleString()}
            label="Total Problems"
            fromColor="#0ea5e9" toColor="#6366f1" glowColor="#0ea5e9"
          />
          <KpiCard
            icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>}
            value={total_attempts.toLocaleString()}
            label="Total Attempts"
            fromColor="#10b981" toColor="#0ea5e9" glowColor="#10b981"
          />
          {/* Solve Rate with SVG ring */}
          <div
            className="relative flex flex-col gap-3 rounded-2xl p-6 overflow-hidden"
            style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', boxShadow: '0 0 40px 0 #f4344318' }}
          >
            <div className="absolute -top-6 -right-6 w-24 h-24 rounded-full blur-2xl pointer-events-none opacity-25 bg-gradient-to-br from-rose-500 to-orange-500" />
            <div className="flex items-center gap-4">
              <div className="relative w-14 h-14 flex-shrink-0">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 48 48">
                  <circle cx="24" cy="24" r="20" fill="transparent" stroke="var(--border)" strokeWidth="3.5" />
                  <circle
                    cx="24" cy="24" r="20" fill="transparent"
                    stroke="url(#roseGrad)" strokeWidth="3.5"
                    strokeLinecap="round"
                    strokeDasharray={2 * Math.PI * 20}
                    strokeDashoffset={2 * Math.PI * 20 * (1 - Math.min(global_solve_rate, 100) / 100)}
                  />
                  <defs>
                    <linearGradient id="roseGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#f43f5e" />
                      <stop offset="100%" stopColor="#fb923c" />
                    </linearGradient>
                  </defs>
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-xs font-black text-rose-400">
                  {global_solve_rate}%
                </span>
              </div>
              <div>
                <p className="text-2xl font-black" style={{ color: 'var(--text-primary)' }}>{global_solve_rate}%</p>
                <p className="text-xs font-bold uppercase tracking-widest mt-1" style={{ color: 'var(--text-secondary)' }}>Solve Rate</p>
              </div>
            </div>
          </div>
        </div>

        {/* ── Platform Health Bar ── */}
        <div className="rounded-2xl p-6 space-y-4" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--text-primary)' }}>
              Submission Success Rate
            </h2>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5 text-emerald-400 font-bold">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block" />
                Passed {successful_attempts?.toLocaleString() || 0}
              </span>
              <span className="flex items-center gap-1.5 text-rose-400 font-bold">
                <span className="w-2.5 h-2.5 rounded-sm bg-rose-500 inline-block" />
                Failed {(total_attempts - (successful_attempts || 0)).toLocaleString()}
              </span>
            </div>
          </div>
          <div className="w-full h-4 rounded-full overflow-hidden flex" style={{ background: 'var(--bg-base)' }}>
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-1000 rounded-l-full"
              style={{ width: `${Math.min(global_solve_rate, 100)}%` }}
            />
            <div
              className="h-full bg-gradient-to-r from-rose-600 to-rose-500 transition-all duration-1000 rounded-r-full"
              style={{ width: `${Math.max(0, 100 - global_solve_rate)}%` }}
            />
          </div>
          <div className="flex justify-between text-[11px] font-bold" style={{ color: 'var(--text-muted)' }}>
            <span>0%</span><span>50%</span><span>100%</span>
          </div>
        </div>

        {/* ── Popular Problems Table ── */}
        <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>
          <div className="px-6 py-4 border-b" style={{ borderColor: 'var(--border)' }}>
            <h2 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--text-primary)' }}>
              Most Attempted Problems
            </h2>
          </div>

          {(!popular_problems || popular_problems.length === 0) ? (
            <div className="p-10 text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
              No attempt data yet.
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr style={{ background: 'var(--bg-surface)' }}>
                  {['Rank', 'Problem', 'Difficulty', 'Attempts', 'Solve Rate', 'Volume'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {popular_problems.map((p, idx) => (
                  <tr
                    key={p.id || idx}
                    className="transition-colors"
                    style={{
                      background: idx % 2 === 0 ? 'transparent' : 'rgba(99,102,241,0.02)',
                      borderTop: '1px solid var(--border)',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--accent-glow)'}
                    onMouseLeave={e => e.currentTarget.style.background = idx % 2 === 0 ? 'transparent' : 'rgba(99,102,241,0.02)'}
                  >
                    <td className="px-5 py-3.5 w-12">
                      <RankBadge rank={idx + 1} />
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{p.title}</span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${DIFF_STYLES[p.difficulty]?.bg || 'text-slate-400'}`}>
                        {cap(p.difficulty)}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-sm font-bold text-indigo-400">{p.attempts?.toLocaleString()}</td>
                    <td className="px-5 py-3.5">
                      <span className={`text-sm font-bold ${p.solve_rate >= 50 ? 'text-emerald-400' : p.solve_rate >= 25 ? 'text-amber-400' : 'text-rose-400'}`}>
                        {p.solve_rate}%
                      </span>
                    </td>
                    <td className="px-5 py-3.5 w-32">
                      <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-base)' }}>
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-700"
                          style={{ width: `${((p.attempts || 0) / maxAttempts) * 100}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* ── Quick Stats Footer ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {[
            { label: 'Avg Attempts / User', value: avgAttemptsPerUser, icon: '⚡', color: 'text-amber-400' },
            { label: 'Problems / User Ratio', value: problemsPerUser, icon: '📐', color: 'text-indigo-400' },
          ].map(stat => (
            <div
              key={stat.label}
              className="flex items-center gap-5 rounded-2xl p-5"
              style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}
            >
              <span className="text-3xl">{stat.icon}</span>
              <div>
                <p className={`text-2xl font-black ${stat.color}`}>{stat.value}</p>
                <p className="text-xs font-bold uppercase tracking-wider mt-0.5" style={{ color: 'var(--text-secondary)' }}>{stat.label}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="h-6" />
      </div>
    </div>
  );
}
