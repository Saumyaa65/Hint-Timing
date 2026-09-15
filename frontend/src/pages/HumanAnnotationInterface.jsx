import React, { useState, useEffect } from 'react';
import apiClient from '../services/apiClient';
import toast, { Toaster } from 'react-hot-toast';

const EVIDENCE_OPTIONS = [
  "Meaningful code change",
  "Error evolved",
  "Tests/results improved",
  "Approach changed",
  "Same error repeated",
  "Same code/approach repeated",
  "No meaningful progress",
  "Exploration without clear progress",
  "Insufficient evidence"
];

export default function HumanAnnotationInterface() {
  const [annotatorId, setAnnotatorId] = useState('Annotator 1');
  const [prefixes, setPrefixes] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showGuidelines, setShowGuidelines] = useState(false);

  // Form State
  const [humanLabel, setHumanLabel] = useState('');
  const [evidence, setEvidence] = useState([]);
  const [confidence, setConfidence] = useState('Medium');

  // Fetch prefixes when annotatorId changes
  useEffect(() => {
    fetchPrefixes();
  }, [annotatorId]);

  const fetchPrefixes = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get(`/human-annotation/prefixes/?annotator_id=${encodeURIComponent(annotatorId)}`);
      setPrefixes(data.prefixes || []);
      if (data.prefixes && data.prefixes.length > 0) {
        // If current index is out of bounds, reset to 0
        const idx = Math.min(currentIndex, data.prefixes.length - 1);
        setCurrentIndex(idx);
        loadAnnotationForPrefix(data.prefixes[idx]);
      }
    } catch (err) {
      console.error("Failed to fetch annotation prefixes", err);
      toast.error("Failed to load trajectory prefixes");
    } finally {
      setLoading(false);
    }
  };

  // Load existing annotation into form when prefix changes or prefixes reloaded
  useEffect(() => {
    if (prefixes.length > 0 && prefixes[currentIndex]) {
      loadAnnotationForPrefix(prefixes[currentIndex]);
    }
  }, [currentIndex, prefixes]);

  const loadAnnotationForPrefix = (prefixObj) => {
    if (prefixObj && prefixObj.existing_annotation) {
      const ann = prefixObj.existing_annotation;
      setHumanLabel(ann.human_label || '');
      setEvidence(ann.evidence || []);
      setConfidence(ann.confidence || 'Medium');
    } else {
      setHumanLabel('');
      setEvidence([]);
      setConfidence('Medium');
    }
  };

  const handleEvidenceToggle = (option) => {
    setEvidence(prev => 
      prev.includes(option) ? prev.filter(item => item !== option) : [...prev, option]
    );
  };

  const handleSubmitAndNext = async () => {
    if (!humanLabel) {
      toast.error("Please select a classification label (Productive, Unproductive, or Uncertain)");
      return;
    }

    const currentPrefix = prefixes[currentIndex];
    if (!currentPrefix) return;

    setSaving(true);
    try {
      await apiClient.post('/human-annotation/submit/', {
        session_id: currentPrefix.session_id,
        prefix_number: currentPrefix.prefix_number,
        annotator_id: annotatorId,
        human_label: humanLabel,
        evidence: evidence,
        confidence: confidence
      });

      toast.success(`Saved prefix ${currentIndex + 1} of ${prefixes.length}`);

      // Update local existing_annotation in state
      const updatedPrefixes = [...prefixes];
      updatedPrefixes[currentIndex].existing_annotation = {
        human_label: humanLabel,
        evidence: evidence,
        confidence: confidence,
        updated_at: new Date().toISOString()
      };
      setPrefixes(updatedPrefixes);

      // Advance to next if not at the end
      if (currentIndex < prefixes.length - 1) {
        setCurrentIndex(prev => prev + 1);
      } else {
        toast("Completed all available trajectory prefixes!", { icon: "🎉" });
      }
    } catch (err) {
      console.error("Failed to submit annotation", err);
      toast.error("Failed to save annotation");
    } finally {
      setSaving(false);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[500px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
          <p className="text-sm text-[var(--text-secondary)] font-medium">Loading research trajectory prefixes...</p>
        </div>
      </div>
    );
  }

  const currentPrefix = prefixes[currentIndex];

  if (!currentPrefix) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-8 max-w-md text-center shadow-xl">
          <h2 className="text-xl font-bold text-[var(--text-primary)] mb-2">No Valid Prefixes Available</h2>
          <p className="text-sm text-[var(--text-secondary)]">There are no valid multi-attempt student sessions loaded for annotation.</p>
        </div>
      </div>
    );
  }

  const totalPrefixes = prefixes.length;

  return (
    <div className="flex-1 flex flex-col overflow-y-auto max-w-5xl mx-auto w-full px-4 py-6 space-y-6">
      <Toaster position="top-right" />

      {/* ── Top Header Controls ── */}
      <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Research Human Annotation Interface
              </span>
              <span className="text-xs text-[var(--text-secondary)]">
                Student ID: <code className="text-indigo-300 font-mono">{currentPrefix.student_user}</code>
              </span>
            </div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">
              Problem: {currentPrefix.problem_title}
            </h1>
            <p className="text-xs text-[var(--text-secondary)] font-mono mt-0.5">
              Session ID: {currentPrefix.session_id}
            </p>
          </div>

          {/* Annotator Switcher */}
          <div className="flex items-center gap-2 bg-[var(--bg-base)] p-1.5 rounded-xl border border-[var(--border)]">
            <span className="text-xs font-semibold text-[var(--text-secondary)] px-2">Annotator:</span>
            {['Annotator 1', 'Annotator 2', 'Annotator 3'].map(id => (
              <button
                key={id}
                onClick={() => setAnnotatorId(id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  annotatorId === id 
                    ? 'bg-indigo-600 text-white shadow-md' 
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                {id}
              </button>
            ))}
          </div>
        </div>

        {/* Progress Tracker Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-sm font-bold text-indigo-400">
              Prefix {currentIndex + 1} of {totalPrefixes}
            </span>
            <span className="text-xs text-[var(--text-secondary)]">
              (Session Step boundary: {currentPrefix.prefix_number} of {currentPrefix.total_prefixes_in_session})
            </span>
            {currentPrefix.existing_annotation && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                ✓ Previously Annotated ({currentPrefix.existing_annotation.human_label})
              </span>
            )}
          </div>

          <button
            onClick={() => setShowGuidelines(!showGuidelines)}
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
          >
            <span>{showGuidelines ? 'Hide Guidelines ▲' : 'Annotation Guidelines ▼'}</span>
          </button>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / totalPrefixes) * 100}%` }}
          />
        </div>
      </div>

      {/* ── Expandable Guidelines Panel ── */}
      {showGuidelines && (
        <div className="bg-slate-900/90 border border-indigo-500/30 rounded-2xl p-6 text-sm text-slate-300 space-y-4 shadow-2xl backdrop-blur-xl animate-fadeIn">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>📖 Annotation Guidelines & Criteria</span>
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-emerald-950/30 border border-emerald-500/30 p-3.5 rounded-xl">
              <span className="font-bold text-emerald-400 text-xs uppercase tracking-wider block mb-1">PRODUCTIVE</span>
              <p className="text-xs text-slate-300">
                The student is making meaningful progress, testing valid hypotheses, learning from errors, or evolving code logic toward a solution.
              </p>
            </div>

            <div className="bg-rose-950/30 border border-rose-500/30 p-3.5 rounded-xl">
              <span className="font-bold text-rose-400 text-xs uppercase tracking-wider block mb-1">UNPRODUCTIVE</span>
              <p className="text-xs text-slate-300">
                The student is stuck in repeated, ineffective behavior with little structural progress (e.g., repeating identical code/errors, thrashing).
              </p>
            </div>

            <div className="bg-amber-950/30 border border-amber-500/30 p-3.5 rounded-xl">
              <span className="font-bold text-amber-400 text-xs uppercase tracking-wider block mb-1">UNCERTAIN</span>
              <p className="text-xs text-slate-300">
                There is insufficient evidence in the prefix to determine whether the struggle is productive or unproductive.
              </p>
            </div>
          </div>

          <div className="bg-indigo-950/20 border border-indigo-500/20 p-3.5 rounded-xl text-xs space-y-1">
            <p className="font-bold text-indigo-300">⚠️ Core Principle: Judge PROCESS, Not Outcome</p>
            <p className="text-slate-300">
              Do not base your judgment on whether the student eventually solved or failed the problem. Judge the trajectory strictly up to the current prefix step. Repeated attempts or identical code should be judged based on the overall evidence in the prefix.
            </p>
          </div>
        </div>
      )}

      {/* ── Chronological Attempt History ── */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--text-secondary)]">
          Trajectory Chronology ({currentPrefix.attempts.length} Attempt Steps in Prefix)
        </h2>

        {currentPrefix.attempts.map((att, idx) => {
          const isLastInPrefix = idx === currentPrefix.attempts.length - 1;
          
          let sourceBadgeColor = "bg-blue-500/10 text-blue-400 border-blue-500/20";
          if (att.source === 'SUBMIT') sourceBadgeColor = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
          if (att.source === 'HINT_REQUEST') sourceBadgeColor = "bg-purple-500/10 text-purple-400 border-purple-500/20";

          return (
            <React.Fragment key={idx}>
              <div className={`bg-[var(--bg-card)] border rounded-2xl p-5 shadow-lg space-y-3 transition-all ${
                isLastInPrefix ? 'border-indigo-500/50 ring-1 ring-indigo-500/30' : 'border-[var(--border)]'
              }`}>
                {/* Step Header */}
                <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-base text-[var(--text-primary)]">
                      ATTEMPT {att.attempt_number}
                    </span>
                    <span className={`px-2.5 py-1 rounded-lg text-xs font-bold border ${sourceBadgeColor}`}>
                      {att.source}
                    </span>
                    {isLastInPrefix && (
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        ⚡ Current Prefix Boundary
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-[var(--text-secondary)] font-mono">
                    {att.created_at}
                  </span>
                </div>

                {/* Code Viewer */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-semibold text-[var(--text-secondary)]">Submitted Code:</span>
                    <span className="text-[10px] text-[var(--text-secondary)] font-mono">JavaScript</span>
                  </div>
                  <pre className="bg-slate-950 text-slate-100 p-4 rounded-xl font-mono text-xs overflow-x-auto border border-slate-800 leading-relaxed">
                    {att.code || "// [No code submitted]"}
                  </pre>
                </div>

                {/* Status & Output */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                  <div className="bg-[var(--bg-base)] p-3 rounded-xl border border-[var(--border)]">
                    <span className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">Execution Status:</span>
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold uppercase ${
                      att.status === 'passed' ? 'bg-emerald-500/20 text-emerald-400' :
                      att.status === 'failed' ? 'bg-rose-500/20 text-rose-400' : 'bg-gray-500/20 text-gray-400'
                    }`}>
                      {att.status}
                    </span>
                    {att.execution_time && (
                      <span className="text-xs text-[var(--text-secondary)] ml-3 font-mono">
                        Time: {att.execution_time}
                      </span>
                    )}
                  </div>

                  {att.evaluation_details && (
                    <div className="bg-[var(--bg-base)] p-3 rounded-xl border border-[var(--border)] overflow-hidden">
                      <span className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">Error / Execution Output:</span>
                      <pre className="text-[11px] font-mono text-slate-300 max-h-24 overflow-y-auto whitespace-pre-wrap">
                        {typeof att.evaluation_details === 'object' 
                          ? JSON.stringify(att.evaluation_details, null, 2) 
                          : String(att.evaluation_details)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>

              {/* Arrow Connector between steps */}
              {!isLastInPrefix && (
                <div className="flex justify-center py-1">
                  <div className="w-8 h-8 rounded-full bg-[var(--bg-card)] border border-[var(--border)] flex items-center justify-center text-[var(--text-secondary)] text-sm shadow-sm">
                    ↓
                  </div>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* ── Annotation Form Section ── */}
      <div className="bg-[var(--bg-card)] border-2 border-indigo-500/40 rounded-2xl p-6 shadow-2xl space-y-6">
        <h2 className="text-lg font-extrabold text-[var(--text-primary)] border-b border-[var(--border)] pb-3 flex items-center gap-2">
          <span>✍️ Human Annotation Section</span>
        </h2>

        {/* 1. Classification Choice */}
        <div className="space-y-3">
          <label className="text-sm font-bold text-[var(--text-primary)] block">
            How would you classify this trajectory prefix? <span className="text-rose-400">*</span>
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { label: 'PRODUCTIVE', desc: 'Student making meaningful progress or logical refinement', color: 'border-emerald-500/50 bg-emerald-500/10 text-emerald-300' },
              { label: 'UNPRODUCTIVE', desc: 'Student stuck in repeated, stagnant or thrashing loops', color: 'border-rose-500/50 bg-rose-500/10 text-rose-300' },
              { label: 'UNCERTAIN', desc: 'Insufficient evidence to determine struggle mode', color: 'border-amber-500/50 bg-amber-500/10 text-amber-300' }
            ].map(opt => (
              <button
                key={opt.label}
                type="button"
                onClick={() => setHumanLabel(opt.label)}
                className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between ${
                  humanLabel === opt.label 
                    ? `${opt.color} ring-2 ring-indigo-500 shadow-lg scale-[1.02]` 
                    : 'border-[var(--border)] bg-[var(--bg-base)] text-[var(--text-secondary)] hover:border-gray-600'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <input
                    type="radio"
                    name="humanLabel"
                    checked={humanLabel === opt.label}
                    onChange={() => setHumanLabel(opt.label)}
                    className="accent-indigo-500"
                  />
                  <span className="font-extrabold text-sm tracking-wide">{opt.label}</span>
                </div>
                <span className="text-[11px] opacity-80 leading-normal">{opt.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 2. Evidence Selection */}
        <div className="space-y-3">
          <label className="text-sm font-bold text-[var(--text-primary)] block">
            What evidence supports your decision? (Select all that apply)
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
            {EVIDENCE_OPTIONS.map(opt => {
              const isChecked = evidence.includes(opt);
              return (
                <button
                  key={opt}
                  type="button"
                  onClick={() => handleEvidenceToggle(opt)}
                  className={`p-3 rounded-xl border text-xs font-medium text-left transition-all flex items-center gap-2.5 ${
                    isChecked
                      ? 'border-indigo-500 bg-indigo-500/15 text-indigo-300 font-bold'
                      : 'border-[var(--border)] bg-[var(--bg-base)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => handleEvidenceToggle(opt)}
                    className="rounded accent-indigo-500 w-4 h-4"
                  />
                  <span>{opt}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 3. Confidence & Annotator ID */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 border-t border-[var(--border)]">
          {/* Confidence */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider block">
              Confidence Level:
            </label>
            <div className="flex gap-2">
              {['Low', 'Medium', 'High'].map(conf => (
                <button
                  key={conf}
                  type="button"
                  onClick={() => setConfidence(conf)}
                  className={`flex-1 py-2 px-3 rounded-xl border text-xs font-bold transition-all ${
                    confidence === conf
                      ? 'border-indigo-500 bg-indigo-600 text-white shadow-md'
                      : 'border-[var(--border)] bg-[var(--bg-base)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                  }`}
                >
                  {conf}
                </button>
              ))}
            </div>
          </div>

          {/* Annotator ID */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider block">
              Active Annotator Identifier:
            </label>
            <input
              type="text"
              value={annotatorId}
              onChange={(e) => setAnnotatorId(e.target.value)}
              placeholder="e.g. Annotator 1"
              className="w-full bg-[var(--bg-base)] border border-[var(--border)] text-[var(--text-primary)] px-3 py-2 rounded-xl text-xs font-mono focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* ── Navigation Footer ── */}
      <div className="flex items-center justify-between pt-2 pb-8">
        <button
          onClick={handlePrevious}
          disabled={currentIndex === 0}
          className="px-6 py-3 rounded-xl border border-[var(--border)] text-sm font-semibold text-[var(--text-primary)] hover:bg-[var(--accent-glow)] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
        >
          ← Previous Prefix
        </button>

        <div className="text-xs text-[var(--text-secondary)] font-mono hidden sm:block">
          Prefix {currentIndex + 1} / {totalPrefixes}
        </div>

        <button
          onClick={handleSubmitAndNext}
          disabled={saving}
          className="px-8 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-sm font-bold shadow-lg shadow-indigo-500/25 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center gap-2"
        >
          {saving ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              <span>Saving...</span>
            </>
          ) : (
            <span>Submit & Next Prefix →</span>
          )}
        </button>
      </div>
    </div>
  );
}
