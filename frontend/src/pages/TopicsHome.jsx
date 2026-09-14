import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import problemService from '../services/problemService';

/* ────────────────────────────────────────────────────────
   Topic Icons — clean minimalist SVGs at configurable size
   ──────────────────────────────────────────────────────── */
const TopicIcon = ({ topic, className = 'w-5 h-5' }) => {
  const n = topic?.toLowerCase() || '';
  const props = { className, fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor', strokeWidth: 1.8 };

  if (n.includes('array'))
    return <svg {...props}><rect x={3} y={3} width={7} height={7} rx={1.5} /><rect x={14} y={3} width={7} height={7} rx={1.5} /><rect x={3} y={14} width={7} height={7} rx={1.5} /><rect x={14} y={14} width={7} height={7} rx={1.5} /></svg>;
  if (n.includes('string'))
    return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M3 5h12M3 10h18M3 15h14M3 20h10" /></svg>;
  if (n.includes('tree') || n.includes('trie'))
    return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v18M12 7l-4 4m4-4l4 4M12 13l-6 6m6-6l6 6" /></svg>;
  if (n.includes('graph'))
    return <svg {...props}><circle cx={12} cy={5} r={3} /><circle cx={5} cy={18} r={3} /><circle cx={19} cy={18} r={3} /><path d="M10 7.5L6.5 15.5M14 7.5l3.5 8M8 18h8" /></svg>;
  if (n.includes('dynamic') || n.includes('dp'))
    return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>;
  if (n.includes('greedy') || n.includes('sort'))
    return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M3 4h13M3 8h9M3 12h5m0 0v8m0-8l-4 4m4-4l4 4" /></svg>;
  if (n.includes('search') || n.includes('find'))
    return <svg {...props}><circle cx={11} cy={11} r={8} /><path strokeLinecap="round" d="M21 21l-4.35-4.35" /></svg>;
  if (n.includes('list') || n.includes('linked'))
    return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>;
  if (n.includes('stack') || n.includes('queue'))
    return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>;
  if (n.includes('hash'))
    return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" /></svg>;
  if (n.includes('matrix'))
    return <svg {...props}><rect x={3} y={3} width={18} height={18} rx={2} /><line x1={3} y1={9} x2={21} y2={9} /><line x1={3} y1={15} x2={21} y2={15} /><line x1={9} y1={3} x2={9} y2={21} /><line x1={15} y1={3} x2={15} y2={21} /></svg>;
  if (n.includes('math'))
    return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M4 4l7 7m0 0l-7 7m7-7h12M20 4l-3 3m3-3l-3-3" /></svg>;
  if (n.includes('sliding') || n.includes('window'))
    return <svg {...props}><rect x={2} y={6} width={20} height={12} rx={2} /><rect x={6} y={8} width={8} height={8} rx={1} className="stroke-current opacity-60" /><path strokeLinecap="round" d="M18 9l2-2m-2 2l2 2" /></svg>;
  if (n.includes('bit'))
    return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>;
  if (n.includes('divide'))
    return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v18m-9-9h18" /><circle cx={6} cy={6} r={2} /><circle cx={18} cy={6} r={2} /><circle cx={6} cy={18} r={2} /><circle cx={18} cy={18} r={2} /></svg>;
  if (n.includes('backtrack') || n.includes('recursion'))
    return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" /></svg>;

  // Default
  return <svg {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>;
};

/* ────────────────────────────────────────────────────────
   Topic colour palette — deterministic per topic name
   ──────────────────────────────────────────────────────── */
const TOPIC_PALETTES = [
  { accent: 'indigo', gradient: 'from-indigo-500/10 to-indigo-600/5', border: 'hover:border-indigo-500/40', text: 'text-indigo-400', iconBg: 'bg-indigo-500/10', glow: 'shadow-indigo-500/5' },
  { accent: 'violet', gradient: 'from-violet-500/10 to-violet-600/5', border: 'hover:border-violet-500/40', text: 'text-violet-400', iconBg: 'bg-violet-500/10', glow: 'shadow-violet-500/5' },
  { accent: 'sky',    gradient: 'from-sky-500/10 to-sky-600/5',       border: 'hover:border-sky-500/40',    text: 'text-sky-400',    iconBg: 'bg-sky-500/10',    glow: 'shadow-sky-500/5' },
  { accent: 'emerald',gradient: 'from-emerald-500/10 to-emerald-600/5',border:'hover:border-emerald-500/40',text: 'text-emerald-400',iconBg: 'bg-emerald-500/10',glow: 'shadow-emerald-500/5' },
  { accent: 'amber',  gradient: 'from-amber-500/10 to-amber-600/5',   border: 'hover:border-amber-500/40',  text: 'text-amber-400',  iconBg: 'bg-amber-500/10',  glow: 'shadow-amber-500/5' },
  { accent: 'rose',   gradient: 'from-rose-500/10 to-rose-600/5',     border: 'hover:border-rose-500/40',   text: 'text-rose-400',   iconBg: 'bg-rose-500/10',   glow: 'shadow-rose-500/5' },
  { accent: 'cyan',   gradient: 'from-cyan-500/10 to-cyan-600/5',     border: 'hover:border-cyan-500/40',   text: 'text-cyan-400',   iconBg: 'bg-cyan-500/10',   glow: 'shadow-cyan-500/5' },
  { accent: 'fuchsia',gradient: 'from-fuchsia-500/10 to-fuchsia-600/5',border:'hover:border-fuchsia-500/40',text:'text-fuchsia-400', iconBg:'bg-fuchsia-500/10', glow: 'shadow-fuchsia-500/5' },
];

const getTopicPalette = (topic) => {
  const hash = topic ? [...topic].reduce((a, c) => a + c.charCodeAt(0), 0) : 0;
  return TOPIC_PALETTES[hash % TOPIC_PALETTES.length];
};

/* ════════════════════════════════════════════════════════
   TopicsHome — Premium Dashboard
   ════════════════════════════════════════════════════════ */
export default function TopicsHome() {
  const [problems, setProblems] = useState([]);
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDifficulty, setSelectedDifficulty] = useState('');
  const [stats, setStats] = useState({
    solvedCount: 0, solvedEasy: 0, solvedMedium: 0, solvedHard: 0, streak: 3
  });
  const [solvedList, setSolvedList] = useState([]);
  const navigate = useNavigate();

  useEffect(() => { loadProblems(); }, []);

  const loadProblems = async () => {
    try {
      setLoading(true);
      const data = await problemService.getAllProblems();
      setProblems(data);
      setTopics([...new Set(data.map(p => p.topic).filter(Boolean))].sort());

      const storedSolved = JSON.parse(localStorage.getItem('solvedProblems') || '[]');
      setSolvedList(storedSolved);
      const solved = data.filter(p => storedSolved.includes(p.problem_id) || storedSolved.includes(p.id?.toString()));
      setStats({
        solvedCount: solvedList.length,
        solvedEasy: solved.filter(p => p.difficulty?.toLowerCase() === 'easy').length,
        solvedMedium: solved.filter(p => p.difficulty?.toLowerCase() === 'medium').length,
        solvedHard: solved.filter(p => p.difficulty?.toLowerCase() === 'hard').length,
        streak: Math.max(3, solvedList.length > 0 ? 5 : 2),
      });
    } catch (error) {
      console.error('Error loading problems:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTopicStats = (topic) => {
    const tp = problems.filter(p => p.topic === topic);
    const solvedCount = tp.filter(p => solvedList.includes(p.problem_id) || solvedList.includes(p.id?.toString())).length;
    return {
      total: tp.length,
      solved: solvedCount,
      easy: tp.filter(p => p.difficulty?.toLowerCase() === 'easy').length,
      medium: tp.filter(p => p.difficulty?.toLowerCase() === 'medium').length,
      hard: tp.filter(p => p.difficulty?.toLowerCase() === 'hard').length,
    };
  };

  const filteredTopics = selectedDifficulty
    ? topics.filter(t => { const s = getTopicStats(t); return s[selectedDifficulty] > 0; })
    : topics;

  const totalProblems = problems.length;
  const totalEasy = problems.filter(p => p.difficulty?.toLowerCase() === 'easy').length;
  const totalMedium = problems.filter(p => p.difficulty?.toLowerCase() === 'medium').length;
  const totalHard = problems.filter(p => p.difficulty?.toLowerCase() === 'hard').length;
  const pct = (a, b) => b > 0 ? (a / b) * 100 : 0;

  /* ── Loading State ── */
  if (loading) {
    return (
      <div className="flex-1 overflow-auto bg-[var(--bg-base)] p-6 md:p-10">
        <div className="max-w-7xl mx-auto space-y-12 animate-pulse">
          {/* Header Skeleton */}
          <div className="flex flex-col md:flex-row gap-8 items-start">
            <div className="flex-1 space-y-4">
              <div className="h-10 w-64 bg-[var(--bg-surface)] rounded-lg" />
              <div className="h-4 w-96 bg-[var(--bg-surface)] rounded-lg" />
            </div>
            <div className="flex gap-4">
              <div className="h-24 w-32 bg-[var(--bg-surface)] rounded-2xl border border-[var(--border)]" />
              <div className="h-24 w-32 bg-[var(--bg-surface)] rounded-2xl border border-[var(--border)]" />
              <div className="h-24 w-32 bg-[var(--bg-surface)] rounded-2xl border border-[var(--border)]" />
            </div>
          </div>
          
          {/* Grid Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-48 bg-[var(--bg-surface)] rounded-2xl border border-[var(--border)]" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto bg-[var(--bg-base)] relative pb-20">
      {/* Ambient background layers */}
      <div className="bg-grid-overlay" />
      <div className="absolute top-0 left-1/4 w-[700px] h-[350px] bg-indigo-500/[0.04] rounded-full blur-[150px] pointer-events-none -z-10" />
      <div className="absolute top-40 right-1/4 w-[500px] h-[300px] bg-purple-500/[0.03] rounded-full blur-[130px] pointer-events-none -z-10" />

      {/* ═══════════════════ HERO BANNER ═══════════════════ */}
      <section className="border-b border-[var(--border)] bg-[var(--bg-surface)]/20 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14 md:py-20">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">

            {/* Left — Hero text */}
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-bold bg-indigo-500/10 border border-indigo-500/25 text-indigo-400 uppercase tracking-widest">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                Adaptive Hint Engine
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-[3.4rem] font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-slate-400 leading-[1.12] tracking-tight">
                Master algorithms. <br />
                <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
                  One hint at a time.
                </span>
              </h1>

              <p className="text-[var(--text-secondary)] max-w-lg text-[15px] leading-relaxed">
                {totalProblems.toLocaleString()} curated challenges across {topics.length} topics.
                Our progressive evaluator delivers targeted conceptual guidance — never spoils the code.
              </p>

              <div className="flex flex-wrap items-center gap-4 pt-1">
                <button
                  onClick={() => navigate('/problems')}
                  className="group px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-300 shadow-lg shadow-indigo-500/20 active:scale-[0.97] inline-flex items-center gap-2"
                >
                  <span>Browse All Problems</span>
                  <svg className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </button>
                <div className="h-5 w-px bg-[var(--border)]" />
                <div className="text-[11px] text-[var(--text-secondary)] font-semibold flex items-center gap-2 bg-[var(--bg-surface)]/60 border border-[var(--border)] px-3.5 py-1.5 rounded-xl">
                  <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse" />
                  <span className="tracking-wider uppercase">{stats.streak}-Day Streak</span>
                </div>
              </div>
            </div>

            {/* Right — Stats panel */}
            <div className="lg:col-span-5">
              <div className="bg-[var(--bg-surface)]/60 border border-[var(--border)] rounded-2xl p-7 shadow-2xl shadow-black/20 relative overflow-hidden">
                <div className="absolute -top-8 -right-8 w-28 h-28 bg-indigo-500/[0.06] rounded-full blur-2xl pointer-events-none" />

                <div className="flex items-center gap-8">
                  {/* Progress ring */}
                  <div className="relative w-28 h-28 flex items-center justify-center flex-shrink-0">
                    <svg className="w-full h-full -rotate-90">
                      <circle cx="56" cy="56" r="48" className="stroke-[var(--bg-elevated)]" strokeWidth="3.5" fill="transparent" />
                      <circle cx="56" cy="56" r="48" className="stroke-indigo-500 transition-all duration-1000" strokeWidth="3.5" fill="transparent"
                        strokeDasharray={2 * Math.PI * 48}
                        strokeDashoffset={2 * Math.PI * 48 * (1 - (stats.solvedCount / Math.max(1, totalProblems)))}
                        strokeLinecap="round"
                        style={{ filter: 'drop-shadow(0 0 6px rgba(99,102,241,0.4))' }}
                      />
                    </svg>
                    <div className="absolute text-center">
                      <span className="text-3xl font-black text-white leading-none block">{stats.solvedCount}</span>
                      <span className="text-[9px] text-[var(--text-muted)] font-bold block uppercase tracking-widest mt-1">/{totalProblems}</span>
                    </div>
                  </div>

                  {/* Difficulty bars */}
                  <div className="flex-1 space-y-4">
                    {[
                      { label: 'Easy',   solved: stats.solvedEasy,   total: totalEasy,   color: 'bg-emerald-500', textColor: 'text-emerald-400' },
                      { label: 'Medium', solved: stats.solvedMedium, total: totalMedium, color: 'bg-amber-500',   textColor: 'text-amber-400' },
                      { label: 'Hard',   solved: stats.solvedHard,   total: totalHard,   color: 'bg-red-500',     textColor: 'text-red-400' },
                    ].map(d => (
                      <div key={d.label} className="space-y-1.5">
                        <div className="flex justify-between text-[11px] font-bold uppercase tracking-wider">
                          <span className={d.textColor}>{d.label}</span>
                          <span className="text-slate-300">{d.solved} <span className="text-slate-600">/ {d.total}</span></span>
                        </div>
                        <div className="w-full h-1.5 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
                          <div className={`${d.color} h-full rounded-full transition-all duration-700`} style={{ width: `${pct(d.solved, d.total)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ═══════════════════ TOPICS GRID ═══════════════════ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">

        {/* Filter bar */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6 mb-10">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Topics</h2>
            <p className="text-[var(--text-secondary)] text-sm mt-1">Select a module to start practicing.</p>
          </div>

          <div className="flex gap-1 bg-[var(--bg-surface)] p-1 border border-[var(--border)] rounded-xl self-start sm:self-center" role="group" aria-label="Difficulty filter">
            {[
              { key: '', label: 'All' },
              { key: 'easy', label: 'Easy', active: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' },
              { key: 'medium', label: 'Medium', active: 'bg-amber-500/10 text-amber-400 border border-amber-500/20' },
              { key: 'hard', label: 'Hard', active: 'bg-red-500/10 text-red-400 border border-red-500/20' },
            ].map(f => (
              <button
                key={f.key}
                onClick={() => setSelectedDifficulty(f.key)}
                className={`px-3.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all duration-200 ${
                  selectedDifficulty === f.key
                    ? (f.active || 'bg-slate-800 text-white border border-slate-700')
                    : 'text-[var(--text-secondary)] hover:text-white'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredTopics.map((topic) => {
            const ts = getTopicStats(topic);
            const pal = getTopicPalette(topic);

            return (
              <div
                key={topic}
                role="button"
                tabIndex={0}
                aria-label={`${topic} — ${ts.total} problems`}
                onClick={() => navigate(`/topics/${encodeURIComponent(topic)}`)}
                onKeyDown={e => e.key === 'Enter' && navigate(`/topics/${encodeURIComponent(topic)}`)}
                className={`group cursor-pointer bg-gradient-to-br ${pal.gradient} backdrop-blur-sm rounded-2xl border border-[var(--border)] ${pal.border} p-6 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl ${pal.glow} focus:outline-none focus:ring-2 focus:ring-indigo-500/30`}
              >
                {/* Card header */}
                <div className="flex items-center justify-between mb-5">
                  <div className="relative">
                    <div className={`w-10 h-10 ${pal.iconBg} rounded-xl flex items-center justify-center border border-[var(--border)] ${pal.text} group-hover:scale-110 transition-transform duration-300`}>
                      <TopicIcon topic={topic} />
                    </div>
                    {/* Small progress ring around the icon */}
                    <svg className="absolute -inset-1.5 w-13 h-13 -rotate-90 pointer-events-none" viewBox="0 0 44 44">
                      <circle cx="22" cy="22" r="20" className="stroke-[var(--bg-elevated)]" strokeWidth="2" fill="transparent" />
                      <circle cx="22" cy="22" r="20" className="stroke-indigo-500 transition-all duration-1000" strokeWidth="2" fill="transparent"
                        strokeDasharray={2 * Math.PI * 20}
                        strokeDashoffset={2 * Math.PI * 20 * (1 - (ts.solved / Math.max(1, ts.total)))}
                        strokeLinecap="round"
                      />
                    </svg>
                  </div>
                  <div className="text-right">
                    <span className="text-2xl font-black text-white tracking-tight">{ts.solved}</span>
                    <span className="text-slate-500 text-lg font-bold">/{ts.total}</span>
                    <span className="text-[9px] text-[var(--text-muted)] font-bold block uppercase tracking-widest">Solved</span>
                  </div>
                </div>

                {/* Title */}
                <h3 className="text-base font-bold text-slate-100 group-hover:text-white transition-colors mb-4">
                  {topic}
                </h3>

                {/* Mini difficulty breakdown */}
                <div className="flex items-center gap-3 text-[10px] font-bold uppercase tracking-wider">
                  <span className="text-emerald-400">{ts.easy} <span className="text-slate-600">E</span></span>
                  <span className="text-slate-700">•</span>
                  <span className="text-amber-400">{ts.medium} <span className="text-slate-600">M</span></span>
                  <span className="text-slate-700">•</span>
                  <span className="text-red-400">{ts.hard} <span className="text-slate-600">H</span></span>
                </div>

                {/* Combined progress bar */}
                <div className="mt-4 w-full h-1.5 bg-[var(--bg-elevated)] rounded-full overflow-hidden flex">
                  {ts.easy > 0 && <div className="bg-emerald-500 h-full transition-all" style={{ width: `${(ts.easy / ts.total) * 100}%` }} />}
                  {ts.medium > 0 && <div className="bg-amber-500 h-full transition-all" style={{ width: `${(ts.medium / ts.total) * 100}%` }} />}
                  {ts.hard > 0 && <div className="bg-red-500 h-full transition-all" style={{ width: `${(ts.hard / ts.total) * 100}%` }} />}
                </div>

                {/* CTA footer */}
                <div className={`mt-5 pt-4 border-t border-[var(--border)]/40 flex items-center justify-between text-xs ${pal.text} font-semibold group-hover:opacity-100 opacity-70 transition-opacity`}>
                  <span className="uppercase text-[10px] tracking-wider">Practice now</span>
                  <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            );
          })}
        </div>

        {/* Empty state */}
        {filteredTopics.length === 0 && (
          <div className="text-center py-20 border border-dashed border-[var(--border)] rounded-2xl bg-[var(--bg-surface)]/10">
            <svg className="w-10 h-10 text-[var(--text-muted)] mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-[var(--text-secondary)] text-sm font-semibold tracking-wider uppercase">No topics match the selected difficulty</p>
          </div>
        )}
      </section>
    </div>
  );
}
