import React, { useState, useEffect, useCallback } from 'react';
import apiClient from '../services/apiClient';

// ─── Medal helpers ─────────────────────────────────────────────────────────────
const MEDAL_EMOJI = { 1: '🥇', 2: '🥈', 3: '🥉' };
const MEDAL_TEXT_COLOR = {
  1: 'text-yellow-400',
  2: 'text-slate-300',
  3: 'text-amber-500',
};
const ROW_GRADIENT = {
  1: 'from-yellow-500/10 via-yellow-400/5 to-transparent border-yellow-500/40',
  2: 'from-slate-400/10 via-slate-300/5 to-transparent border-slate-400/40',
  3: 'from-amber-600/10 via-amber-500/5 to-transparent border-amber-600/40',
};
const SCORE_BAR_COLOR = {
  1: 'from-yellow-400 to-yellow-600',
  2: 'from-slate-300 to-slate-500',
  3: 'from-amber-500 to-amber-700',
};

function RankBadge({ rank }) {
  if (rank <= 3) {
    return (
      <span className={`text-2xl leading-none select-none ${MEDAL_TEXT_COLOR[rank]}`}>
        {MEDAL_EMOJI[rank]}
      </span>
    );
  }
  return (
    <span
      className="text-sm font-semibold tabular-nums"
      style={{ color: 'var(--text-secondary)' }}
    >
      #{rank}
    </span>
  );
}

function ScoreBar({ score, maxScore, rank }) {
  const pct = maxScore > 0 ? Math.min((score / maxScore) * 100, 100) : 0;
  const gradient = SCORE_BAR_COLOR[rank] ?? 'from-indigo-500 to-violet-600';

  return (
    <div className="flex items-center gap-3 w-full">
      <div
        className="flex-1 rounded-full h-1.5 overflow-hidden"
        style={{ background: 'var(--border)' }}
      >
        <div
          className={`h-full rounded-full bg-gradient-to-r ${gradient} transition-all duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span
        className="text-sm font-bold tabular-nums min-w-[3rem] text-right"
        style={{ color: 'var(--text-primary)' }}
      >
        {score.toLocaleString()}
      </span>
    </div>
  );
}

// ─── Skeleton row ──────────────────────────────────────────────────────────────
function SkeletonRow({ index }) {
  return (
    <div
      className="animate-pulse flex items-center gap-4 px-5 py-4 rounded-xl border"
      style={{
        background: 'var(--bg-surface)',
        borderColor: 'var(--border)',
        animationDelay: `${index * 60}ms`,
      }}
    >
      <div className="w-8 h-5 rounded" style={{ background: 'var(--bg-elevated)' }} />
      <div className="flex-1 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full" style={{ background: 'var(--bg-elevated)' }} />
        <div className="h-4 rounded w-32" style={{ background: 'var(--bg-elevated)' }} />
      </div>
      <div className="flex-1 hidden sm:flex items-center gap-3">
        <div className="flex-1 h-1.5 rounded-full" style={{ background: 'var(--bg-elevated)' }} />
        <div className="w-14 h-4 rounded" style={{ background: 'var(--bg-elevated)' }} />
      </div>
    </div>
  );
}

// ─── Avatar initials ───────────────────────────────────────────────────────────
function Avatar({ username }) {
  const letter = username?.[0]?.toUpperCase() ?? '?';
  const gradients = [
    'from-indigo-500 to-violet-600',
    'from-emerald-500 to-teal-600',
    'from-pink-500 to-rose-600',
    'from-amber-500 to-orange-600',
    'from-sky-500 to-cyan-600',
  ];
  const g = gradients[(username?.charCodeAt(0) ?? 0) % gradients.length];

  return (
    <div
      className={`w-9 h-9 rounded-full bg-gradient-to-br ${g} flex items-center justify-center text-white text-sm font-bold flex-shrink-0 shadow-md`}
    >
      {letter}
    </div>
  );
}

// ─── Leaderboard row ───────────────────────────────────────────────────────────
function LeaderboardRow({ entry, maxScore, isTop3 }) {
  const { rank, username, score } = entry;
  const rowStyle = isTop3
    ? `bg-gradient-to-r ${ROW_GRADIENT[rank]} border`
    : 'border hover:border-indigo-500/30 hover:bg-indigo-500/5 transition-colors duration-200';

  return (
    <div
      className={`flex items-center gap-4 px-5 py-4 rounded-xl ${rowStyle}`}
      style={
        isTop3
          ? {}
          : { background: 'var(--bg-surface)', borderColor: 'var(--border)' }
      }
    >
      {/* Rank */}
      <div className="w-8 flex items-center justify-center flex-shrink-0">
        <RankBadge rank={rank} />
      </div>

      {/* Avatar + Username */}
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <Avatar username={username} rank={rank} />
        <span
          className={`font-semibold truncate ${
            isTop3 ? 'text-base' : 'text-sm'
          }`}
          style={{ color: 'var(--text-primary)' }}
        >
          {username}
        </span>
      </div>

      {/* Score bar */}
      <div className="flex-1 hidden sm:flex">
        <ScoreBar score={score} maxScore={maxScore} rank={rank} />
      </div>

      {/* Mobile score */}
      <div className="sm:hidden flex-shrink-0">
        <span
          className="text-sm font-bold tabular-nums"
          style={{ color: 'var(--text-primary)' }}
        >
          {score.toLocaleString()}
        </span>
      </div>
    </div>
  );
}

// ─── Trophy icon ───────────────────────────────────────────────────────────────
function TrophyIcon({ className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
    >
      <path
        fillRule="evenodd"
        d="M5.166 2.621v.858c-1.035.148-2.059.33-3.071.543a.75.75 0 0 0-.584.859 6.753 6.753 0 0 0 6.138 5.6 6.73 6.73 0 0 0 2.743 1.346A6.707 6.707 0 0 1 9.279 15H8.54c-1.036 0-1.875.84-1.875 1.875V19.5h-.75a2.25 2.25 0 0 0-2.25 2.25c0 .414.336.75.75.75h15a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-2.25-2.25h-.75v-2.625c0-1.036-.84-1.875-1.875-1.875h-.739a6.706 6.706 0 0 1-1.112-3.173 6.73 6.73 0 0 0 2.743-1.347 6.753 6.753 0 0 0 6.139-5.6.75.75 0 0 0-.585-.858 47.077 47.077 0 0 0-3.07-.543V2.62a.75.75 0 0 0-.658-.744 49.798 49.798 0 0 0-6.093-.377c-2.063 0-4.096.128-6.093.377a.75.75 0 0 0-.657.744Zm0 2.629c0 1.196.312 2.32.857 3.294A5.266 5.266 0 0 1 3.16 5.337a45.6 45.6 0 0 1 2.006-.343v.256Zm13.5 0v-.256c.674.1 1.343.214 2.006.343a5.265 5.265 0 0 1-2.863 3.207 6.72 6.72 0 0 0 .857-3.294Z"
        clipRule="evenodd"
      />
    </svg>
  );
}

// ─── Refresh icon ──────────────────────────────────────────────────────────────
function RefreshIcon({ spinning, className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`${className} ${spinning ? 'animate-spin' : ''}`}
    >
      <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
      <path d="M21 3v5h-5" />
      <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
      <path d="M8 16H3v5" />
    </svg>
  );
}

// ─── Main page ─────────────────────────────────────────────────────────────────
export default function Leaderboard() {
  const [rankings, setRankings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchRankings = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get('/leaderboard/global_rankings/');
      const sorted = (Array.isArray(data) ? data : [])
        .sort((a, b) => a.rank - b.rank)
        .slice(0, 100);
      setRankings(sorted);
    } catch (err) {
      setError(err?.message ?? 'Failed to load leaderboard. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchRankings(false);
  }, [fetchRankings]);

  const maxScore =
    rankings.length > 0 ? Math.max(...rankings.map((r) => r.score)) : 0;

  return (
    <div
      className="min-h-screen overflow-y-auto"
      style={{ background: 'var(--bg-base)' }}
    >
      <div className="max-w-4xl mx-auto px-4 py-10">

        {/* ── Hero Header ── */}
        <div className="relative mb-10">
          {/* Ambient glow */}
          <div
            className="absolute -top-10 left-1/2 -translate-x-1/2 w-80 h-40 rounded-full blur-3xl opacity-20 pointer-events-none"
            style={{ background: 'var(--accent-glow, #6366f1)' }}
          />

          <div className="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            {/* Title block */}
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-violet-600/20 border border-indigo-500/30 backdrop-blur-sm shadow-lg shadow-indigo-500/10">
                <TrophyIcon className="w-7 h-7 text-yellow-400" />
              </div>
              <div>
                <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
                  Global Leaderboard
                </h1>
                <p className="mt-0.5 text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Top 100 coders ranked by score
                </p>
              </div>
            </div>

            {/* Refresh button */}
            <button
              onClick={() => fetchRankings(true)}
              disabled={loading || refreshing}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border transition-all duration-200
                         hover:border-indigo-500/60 hover:bg-indigo-500/10 hover:text-indigo-300
                         disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: 'var(--bg-surface)',
                borderColor: 'var(--border)',
                color: 'var(--text-secondary)',
              }}
            >
              <RefreshIcon spinning={refreshing} className="w-4 h-4" />
              {refreshing ? 'Refreshing\u2026' : 'Refresh'}
            </button>
          </div>

          {/* Divider */}
          <div
            className="mt-8 h-px w-full rounded-full"
            style={{
              background:
                'linear-gradient(to right, transparent, var(--border), transparent)',
            }}
          />
        </div>

        {/* ── Loading Skeleton ── */}
        {loading && (
          <div className="space-y-3">
            {Array.from({ length: 10 }).map((_, i) => (
              <SkeletonRow key={i} index={i} />
            ))}
          </div>
        )}

        {/* ── Error State ── */}
        {!loading && error && (
          <div className="flex flex-col items-center justify-center py-24 gap-5 text-center">
            <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="w-10 h-10 text-red-400"
              >
                <path
                  fillRule="evenodd"
                  d="M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003ZM12 8.25a.75.75 0 0 1 .75.75v3.75a.75.75 0 0 1-1.5 0V9a.75.75 0 0 1 .75-.75Zm0 8.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div>
              <p className="text-lg font-semibold text-red-400">Something went wrong</p>
              <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
                {error}
              </p>
            </div>
            <button
              onClick={() => fetchRankings(false)}
              className="px-5 py-2 rounded-xl text-sm font-semibold bg-gradient-to-r from-indigo-500 to-violet-600 text-white hover:from-indigo-400 hover:to-violet-500 transition-all duration-200 shadow-lg shadow-indigo-500/25"
            >
              Try Again
            </button>
          </div>
        )}

        {/* ── Empty State ── */}
        {!loading && !error && rankings.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 gap-5 text-center">
            <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
              <TrophyIcon className="w-10 h-10 text-indigo-400 opacity-50" />
            </div>
            <div>
              <p className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                No rankings yet
              </p>
              <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
                Be the first to solve problems and claim the top spot!
              </p>
            </div>
          </div>
        )}

        {/* ── Rankings Table ── */}
        {!loading && !error && rankings.length > 0 && (
          <>
            {/* Column headers */}
            <div
              className="flex items-center gap-4 px-5 pb-2 mb-2 text-xs font-semibold uppercase tracking-widest"
              style={{ color: 'var(--text-secondary)' }}
            >
              <div className="w-8 text-center">Rank</div>
              <div className="flex-1">User</div>
              <div className="flex-1 hidden sm:block">Score</div>
              <div className="sm:hidden">Score</div>
            </div>

            {/* Podium (top 3) */}
            {rankings.slice(0, 3).length > 0 && (
              <div className="space-y-2 mb-2">
                {rankings.slice(0, 3).map((entry) => (
                  <LeaderboardRow
                    key={entry.clerk_id ?? entry.username}
                    entry={entry}
                    maxScore={maxScore}
                    isTop3={true}
                  />
                ))}
              </div>
            )}

            {/* Separator */}
            {rankings.length > 3 && (
              <div className="flex items-center gap-3 my-4">
                <div
                  className="flex-1 h-px"
                  style={{ background: 'var(--border)' }}
                />
                <span
                  className="text-xs font-medium tracking-widest uppercase px-2"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  Challengers
                </span>
                <div
                  className="flex-1 h-px"
                  style={{ background: 'var(--border)' }}
                />
              </div>
            )}

            {/* Rest (rank 4-100) */}
            {rankings.length > 3 && (
              <div className="space-y-2">
                {rankings.slice(3).map((entry) => (
                  <LeaderboardRow
                    key={entry.clerk_id ?? entry.username}
                    entry={entry}
                    maxScore={maxScore}
                    isTop3={false}
                  />
                ))}
              </div>
            )}

            {/* Footer note */}
            <p
              className="mt-8 text-center text-xs"
              style={{ color: 'var(--text-secondary)' }}
            >
              Showing top {rankings.length} coders \u00b7 Updated in real-time
            </p>
          </>
        )}
      </div>
    </div>
  );
}
