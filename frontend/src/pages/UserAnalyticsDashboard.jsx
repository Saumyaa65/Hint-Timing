import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../services/apiClient';

/* ─────────────────────────────────────────────────────────
   HEATMAP HELPER – generate 84-cell pseudo-random grid
───────────────────────────────────────────────────────── */
function generateHeatmap(solveCount) {
  const TOTAL = 84;
  const cells = Array(TOTAL).fill(0);
  const filled = Math.min(solveCount, TOTAL);
  let placed = 0;
  // Bias toward recent (higher-index) cells
  for (let i = TOTAL - 1; i >= 0 && placed < filled; i--) {
    if (Math.random() < ((i + 1) / TOTAL) * 1.8) {
      cells[i] = Math.random() > 0.5 ? 2 : 1;
      placed++;
    }
  }
  // Fill stragglers
  for (let i = 0; i < TOTAL && placed < filled; i++) {
    if (!cells[i]) { cells[i] = 1; placed++; }
  }
  return cells;
}

const HEAT_BG = {
  0: { background: 'var(--bg-elevated)', opacity: 0.6 },
  1: { background: '#6366f1',            opacity: 0.7 },
  2: { background: '#a78bfa',            opacity: 0.95 },
};

/* ─────────────────────────────────────────────────────────
   STAT CARD
───────────────────────────────────────────────────────── */
function StatCard({ icon, value, label, from, to, glow }) {
  return (
    <div
      className="relative flex flex-col items-center justify-center gap-2 rounded-2xl p-6 overflow-hidden"
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: `0 0 36px 0 ${glow}1a`,
      }}
    >
      {/* Corner glow blob */}
      <div
        className="absolute -top-8 -right-8 w-28 h-28 rounded-full blur-3xl pointer-events-none"
        style={{ background: `linear-gradient(135deg,${from},${to})`, opacity: 0.18 }}
      />

      {/* Icon pill */}
      <div
        className="text-3xl w-14 h-14 flex items-center justify-center rounded-xl"
        style={{
          background: `linear-gradient(135deg,${from}2a,${to}2a)`,
          border: `1px solid ${from}55`,
        }}
      >
        {icon}
      </div>

      {/* Number */}
      <span className="text-4xl font-black tabular-nums" style={{ color: from }}>
        {value ?? '—'}
      </span>

      {/* Label */}
      <span
        className="text-xs font-semibold uppercase tracking-widest text-center"
        style={{ color: 'var(--text-secondary)' }}
      >
        {label}
      </span>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────
   STREAK BOX
───────────────────────────────────────────────────────── */
function StreakBox({ icon, value, title, subtitle }) {
  return (
    <div
      className="flex-1 flex flex-col items-center justify-center gap-3 rounded-2xl p-8"
      style={{
        background: 'linear-gradient(135deg,#1c1008 0%,#0f172a 100%)',
        border: '1.5px solid #f9731699',
        boxShadow: '0 0 48px 0 #f9731618',
      }}
    >
      <span className="text-5xl select-none">{icon}</span>
      <span
        className="text-6xl font-black tabular-nums"
        style={{
          background: 'linear-gradient(90deg,#f97316,#fbbf24)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}
      >
        {value ?? 0}
      </span>
      <div className="text-center space-y-0.5">
        <p className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{title}</p>
        <p className="text-xs"        style={{ color: 'var(--text-secondary)' }}>{subtitle}</p>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────
   ACTIVITY HEATMAP
───────────────────────────────────────────────────────── */
function ActivityHeatmap({ solveCount }) {
  const WEEKS = 12;
  const DAYS  = 7;
  const DAY_LABELS = ['Mon', '', 'Wed', '', 'Fri', '', ''];

  const cells = useMemo(() => generateHeatmap(solveCount), [solveCount]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-2 items-start">
        {/* Day labels */}
        <div className="flex flex-col gap-1.5 pt-0.5 select-none" style={{ minWidth: 26 }}>
          {DAY_LABELS.map((d, i) => (
            <span
              key={i}
              className="h-3 flex items-center"
              style={{ color: 'var(--text-secondary)', fontSize: 10, lineHeight: '12px' }}
            >
              {d}
            </span>
          ))}
        </div>

        {/* Grid */}
        <div className="flex gap-1.5">
          {Array.from({ length: WEEKS }).map((_, w) => (
            <div key={w} className="flex flex-col gap-1.5">
              {Array.from({ length: DAYS }).map((_, d) => {
                const intensity = cells[w * DAYS + d];
                return (
                  <div
                    key={d}
                    className="w-3 h-3 rounded-sm transition-transform duration-150 hover:scale-125 cursor-default"
                    style={HEAT_BG[intensity] ?? HEAT_BG[0]}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-2">
        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Less</span>
        {[0, 1, 2].map(i => (
          <div key={i} className="w-3 h-3 rounded-sm" style={HEAT_BG[i]} />
        ))}
        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>More</span>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────
   TOPIC ROW
───────────────────────────────────────────────────────── */
function TopicRow({ topic, mastery_level, problems_solved }) {
  const pct = Math.round((mastery_level ?? 0) * 100);
  const barColor =
    pct >= 70 ? 'linear-gradient(90deg,#10b981,#34d399)'
    : pct >= 40 ? 'linear-gradient(90deg,#f59e0b,#fbbf24)'
    :             'linear-gradient(90deg,#6366f1,#8b5cf6)';
  const pctColor = pct >= 70 ? '#34d399' : pct >= 40 ? '#fbbf24' : '#f87171';

  return (
    <div
      className="flex flex-col gap-2 p-4 rounded-xl"
      style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}
    >
      <div className="flex items-center justify-between">
        <span className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{topic}</span>
        <div className="flex items-center gap-2">
          <span
            className="text-xs font-bold px-2 py-0.5 rounded-full"
            style={{ background: '#6366f118', color: '#818cf8', border: '1px solid #6366f140' }}
          >
            {problems_solved} solved
          </span>
          <span className="text-xs font-black" style={{ color: pctColor }}>{pct}%</span>
        </div>
      </div>
      <div className="w-full h-2 rounded-full overflow-hidden" style={{ background: 'var(--bg-base)' }}>
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: barColor }}
        />
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────
   LOADING SKELETON
───────────────────────────────────────────────────────── */
function Bone({ className = '' }) {
  return (
    <div
      className={`animate-pulse rounded-xl ${className}`}
      style={{ background: 'var(--bg-elevated)' }}
    />
  );
}

function LoadingState() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8 w-full space-y-8">
      <Bone className="h-12 w-52" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => <Bone key={i} className="h-44" />)}
      </div>
      <Bone className="h-10 w-full" />
      <div className="flex gap-4">
        <Bone className="flex-1 h-52" />
        <Bone className="flex-1 h-52" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Bone className="h-48" />
        <Bone className="h-48" />
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────
   MAIN COMPONENT
───────────────────────────────────────────────────────── */
export default function UserAnalyticsDashboard() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    apiClient
      .get('/analytics/user_dashboard/')
      .then(res => {
        if (!cancelled) { setData(res.data); setLoading(false); }
      })
      .catch(err => {
        if (!cancelled) {
          setError(err?.response?.data?.detail || 'Failed to load analytics. Please try again.');
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, []);

  /* ── Loading ── */
  if (loading) return <LoadingState />;

  /* ── Error ── */
  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 w-full flex flex-col items-center justify-center gap-4 min-h-64">
        <span className="text-5xl">⚠️</span>
        <p className="text-base font-semibold" style={{ color: '#f87171' }}>{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-5 py-2 rounded-lg text-sm font-bold transition-all hover:opacity-90"
          style={{ background: 'linear-gradient(90deg,#6366f1,#8b5cf6)', color: '#fff' }}
        >
          Retry
        </button>
      </div>
    );
  }

  const {
    total_attempts      = 0,
    successful_attempts = 0,
    solve_rate          = 0,
    hints_used          = 0,
    topic_stats         = [],
    current_streak      = 0,
    longest_streak      = 0,
  } = data || {};

  return (
    <div
      className="max-w-7xl mx-auto px-4 py-8 w-full overflow-y-auto animate-fade-in-up"
      style={{ minHeight: '100vh' }}
    >
      {/* ══ PAGE TITLE ══════════════════════════════════════════ */}
      <div className="mb-8">
        <h1
          className="text-4xl md:text-5xl font-black tracking-tight"
          style={{
            background: 'linear-gradient(90deg,#818cf8,#a78bfa,#c084fc)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          My Dashboard
        </h1>
        <p className="mt-1.5 text-sm" style={{ color: 'var(--text-secondary)' }}>
          Track your progress, streaks, and topic mastery at a glance.
        </p>
      </div>

      {/* ══ SECTION 1 · HERO STAT CARDS ════════════════════════ */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
        <StatCard icon="📊" value={total_attempts}      label="Total Attempts"   from="#6366f1" to="#818cf8" glow="#6366f1" />
        <StatCard icon="✅" value={successful_attempts} label="Problems Solved"  from="#10b981" to="#34d399" glow="#10b981" />
        <StatCard icon="🔥" value={current_streak}      label="Current Streak"   from="#f97316" to="#fbbf24" glow="#f97316" />
        <StatCard icon="💡" value={hints_used}          label="Hints Used"       from="#a855f7" to="#c084fc" glow="#a855f7" />
      </section>

      {/* Solve-rate accent bar */}
      <div
        className="mb-6 rounded-xl px-5 py-3 flex items-center gap-4"
        style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)' }}
      >
        <span className="text-sm font-semibold whitespace-nowrap" style={{ color: 'var(--text-secondary)' }}>
          Overall Solve Rate
        </span>
        <div className="flex-1 h-2.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-base)' }}>
          <div
            className="h-full rounded-full transition-all duration-1000"
            style={{
              width: `${Math.min(Number(solve_rate), 100)}%`,
              background: 'linear-gradient(90deg,#6366f1,#a855f7,#ec4899)',
            }}
          />
        </div>
        <span className="text-sm font-black w-14 text-right tabular-nums" style={{ color: '#a78bfa' }}>
          {Number(solve_rate).toFixed(1)}%
        </span>
      </div>

      {/* ══ SECTION 2 · STREAK TRACKER ═════════════════════════ */}
      <section className="mb-6">
        <h2
          className="text-base font-bold mb-3 flex items-center gap-2"
          style={{ color: 'var(--text-primary)' }}
        >
          🔥 Streak Tracker
        </h2>
        <div className="flex gap-4">
          <StreakBox icon="🔥" value={current_streak} title="Current Streak" subtitle="Keep it going!" />
          <StreakBox icon="🏆" value={longest_streak} title="Longest Streak" subtitle="Personal best"  />
        </div>
      </section>

      {/* ══ SECTIONS 3 + 4 · HEATMAP & TOPICS ═════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

        {/* Activity Heatmap */}
        <section
          className="rounded-2xl p-6"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)' }}
        >
          <h2
            className="text-base font-bold mb-4 flex items-center gap-2"
            style={{ color: 'var(--text-primary)' }}
          >
            📅 Activity — Last 12 Weeks
          </h2>
          <ActivityHeatmap solveCount={successful_attempts} />
        </section>

        {/* Topic Mastery */}
        <section
          className="rounded-2xl p-6"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)' }}
        >
          <h2
            className="text-base font-bold mb-4 flex items-center gap-2"
            style={{ color: 'var(--text-primary)' }}
          >
            🎯 Topic Mastery
          </h2>

          {topic_stats.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 gap-3">
              <span className="text-4xl select-none">🌱</span>
              <p className="text-sm text-center" style={{ color: 'var(--text-secondary)' }}>
                Start solving to see your topic mastery
              </p>
              <Link
                to="/problems"
                className="mt-1 px-4 py-1.5 rounded-lg text-xs font-semibold hover:opacity-90 transition-opacity"
                style={{ background: 'linear-gradient(90deg,#6366f1,#8b5cf6)', color: '#fff' }}
              >
                Browse Problems
              </Link>
            </div>
          ) : (
            <div className="flex flex-col gap-3 overflow-y-auto pr-1" style={{ maxHeight: 260 }}>
              {topic_stats.map((t, i) => <TopicRow key={i} {...t} />)}
            </div>
          )}
        </section>
      </div>

      {/* ══ SECTION 5 · QUICK ACTIONS ══════════════════════════ */}
      <section
        className="rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4"
        style={{
          background: 'linear-gradient(135deg,#1e1b4b 0%,#0f172a 100%)',
          border: '1px solid #4f46e555',
          boxShadow: '0 0 48px 0 #6366f10e',
        }}
      >
        <div>
          <p className="text-base font-bold" style={{ color: 'var(--text-primary)' }}>
            Ready to keep pushing?
          </p>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>
            Pick up where you left off or see how you rank.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Link
            to="/problems"
            className="px-5 py-2.5 rounded-xl text-sm font-bold transition-transform hover:scale-105 active:scale-95"
            style={{
              background: 'linear-gradient(90deg,#6366f1,#8b5cf6)',
              color: '#fff',
              boxShadow: '0 4px 20px 0 #6366f140',
            }}
          >
            Browse Problems
          </Link>
          <Link
            to="/leaderboard"
            className="px-5 py-2.5 rounded-xl text-sm font-bold transition-transform hover:scale-105 active:scale-95"
            style={{
              background: 'var(--bg-elevated)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border)',
            }}
          >
            View Leaderboard
          </Link>
        </div>
      </section>

      <div className="h-10" />
    </div>
  );
}
