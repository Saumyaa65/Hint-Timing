import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
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
        <div className="w-9 h-9 rounded-full" style={{ background: 'var(--bg-surface)' }} />
        <div className="h-3 w-32 rounded" style={{ background: 'var(--bg-surface)' }} />
        <div className="ml-auto h-3 w-16 rounded" style={{ background: 'var(--bg-surface)' }} />
      </div>
      <div className="h-4 w-2/3 rounded" style={{ background: 'var(--bg-surface)' }} />
      <div className="h-3 w-full rounded" style={{ background: 'var(--bg-surface)' }} />
      <div className="h-3 w-4/5 rounded" style={{ background: 'var(--bg-surface)' }} />
      <div className="flex items-center gap-3 pt-2">
        <div className="h-8 w-20 rounded-xl" style={{ background: 'var(--bg-surface)' }} />
        <div className="h-6 w-14 rounded" style={{ background: 'var(--bg-surface)' }} />
      </div>
    </div>
  );
}

/* ─── comment block ─── */
function CommentItem({ comment }) {
  return (
    <div className="flex gap-3 pt-3">
      <div
        className="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-black text-white mt-0.5"
        style={{ background: `hsl(${(comment.username?.charCodeAt(0) || 0) * 15}, 60%, 45%)` }}
      >
        {(comment.username || 'A').charAt(0).toUpperCase()}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold" style={{ color: 'var(--text-primary)' }}>{comment.username}</span>
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{timeAgo(comment.created_at)}</span>
        </div>
        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{comment.content}</p>
      </div>
    </div>
  );
}

export default function Forum() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState({}); // { [id]: bool }
  const [showNewForm, setShowNewForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [upvoted, setUpvoted] = useState({});
  const [commentInputs, setCommentInputs] = useState({});
  const [submittingComment, setSubmittingComment] = useState({});

  useEffect(() => { fetchPosts(); }, []);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.get('/forums/');
      setPosts(Array.isArray(data) ? data : (data.results || []));
    } catch (err) {
      console.error('Failed to load forum posts', err);
      setError('Failed to load posts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePost = async (e) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) return;
    try {
      setIsSubmitting(true);
      await apiClient.post('/forums/', { title: newTitle.trim(), content: newContent.trim() });
      setNewTitle('');
      setNewContent('');
      setShowNewForm(false);
      fetchPosts();
    } catch (err) {
      console.error('Failed to create post', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpvote = async (postId) => {
    if (upvoted[postId]) return;
    try {
      await apiClient.post(`/forums/${postId}/upvote/`);
      setUpvoted(prev => ({ ...prev, [postId]: true }));
      setPosts(prev => prev.map(p => p.id === postId ? { ...p, upvotes: (p.upvotes || 0) + 1 } : p));
    } catch (e) {
      console.error('Upvote failed', e);
    }
  };

  const handleComment = async (postId) => {
    const content = (commentInputs[postId] || '').trim();
    if (!content) return;
    try {
      setSubmittingComment(prev => ({ ...prev, [postId]: true }));
      await apiClient.post(`/forums/${postId}/comment/`, { content });
      setCommentInputs(prev => ({ ...prev, [postId]: '' }));
      fetchPosts();
    } catch (e) {
      console.error('Comment failed', e);
    } finally {
      setSubmittingComment(prev => ({ ...prev, [postId]: false }));
    }
  };

  const toggleExpand = (id) => setExpanded(prev => ({ ...prev, [id]: !prev[id] }));

  return (
    <div className="flex-1 overflow-y-auto pb-20" style={{ background: 'var(--bg-base)' }}>
      {/* Ambient glow */}
      <div className="fixed top-24 right-1/4 w-[600px] h-[350px] bg-indigo-500/[0.04] rounded-full blur-[160px] pointer-events-none -z-10" />
      <div className="fixed bottom-1/4 left-1/4 w-[400px] h-[250px] bg-violet-500/[0.03] rounded-full blur-[140px] pointer-events-none -z-10" />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8 animate-fade-in-up">

        {/* ── Hero Header ── */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 mb-3 rounded-full text-[10px] font-bold bg-indigo-500/10 border border-indigo-500/25 text-indigo-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
              Community
            </div>
            <h1 className="text-3xl md:text-4xl font-black bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
              Community Forum
            </h1>
            <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
              Ask questions, share insights, and discuss problems with the community
            </p>
          </div>
          <button
            onClick={() => setShowNewForm(v => !v)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all hover:scale-105 active:scale-95 ${
              showNewForm
                ? 'bg-slate-700 text-slate-300 border border-slate-600'
                : 'bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-lg shadow-indigo-500/20'
            }`}
          >
            {showNewForm ? (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                Cancel
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                New Post
              </>
            )}
          </button>
        </div>

        {/* ── New Post Form ── */}
        {showNewForm && (
          <form
            onSubmit={handleCreatePost}
            className="rounded-2xl p-6 space-y-4"
            style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', boxShadow: '0 0 40px rgba(99,102,241,0.08)' }}
          >
            <h2 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--text-primary)' }}>Create a Post</h2>
            <input
              type="text"
              placeholder="Post title…"
              value={newTitle}
              onChange={e => setNewTitle(e.target.value)}
              required
              className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all"
              style={{
                background: 'var(--bg-base)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
              }}
              onFocus={e => e.target.style.borderColor = 'rgba(99,102,241,0.5)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
            <textarea
              placeholder="Share your thoughts, questions, or approach…"
              value={newContent}
              onChange={e => setNewContent(e.target.value)}
              required
              rows={5}
              className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all resize-none"
              style={{
                background: 'var(--bg-base)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
              }}
              onFocus={e => e.target.style.borderColor = 'rgba(99,102,241,0.5)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowNewForm(false)}
                className="px-4 py-2 rounded-xl text-sm font-bold transition-colors"
                style={{ color: 'var(--text-secondary)', background: 'var(--bg-surface)', border: '1px solid var(--border)' }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !newTitle.trim() || !newContent.trim()}
                className="px-5 py-2 rounded-xl text-sm font-bold transition-all disabled:opacity-50 active:scale-95 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white"
              >
                {isSubmitting ? 'Posting…' : 'Publish Post'}
              </button>
            </div>
          </form>
        )}

        {/* ── Stats row ── */}
        {!loading && !error && posts.length > 0 && (
          <div className="flex items-center gap-4 text-xs font-bold" style={{ color: 'var(--text-muted)' }}>
            <span>{posts.length} discussion{posts.length !== 1 ? 's' : ''}</span>
            <span>•</span>
            <span>{posts.reduce((acc, p) => acc + (p.comments?.length || 0), 0)} replies</span>
          </div>
        )}

        {/* ── Loading ── */}
        {loading && (
          <div className="space-y-5">
            {[0, 1, 2].map(i => <SkeletonCard key={i} />)}
          </div>
        )}

        {/* ── Error ── */}
        {!loading && error && (
          <div className="text-center py-16 space-y-4">
            <svg className="w-12 h-12 text-rose-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{error}</p>
            <button onClick={fetchPosts} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg transition-colors">
              Try Again
            </button>
          </div>
        )}

        {/* ── Empty ── */}
        {!loading && !error && posts.length === 0 && (
          <div className="text-center py-24 rounded-2xl border border-dashed" style={{ borderColor: 'var(--border)' }}>
            <svg className="w-14 h-14 mx-auto mb-4 opacity-25" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: 'var(--text-muted)' }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-base font-bold mb-1" style={{ color: 'var(--text-primary)' }}>No discussions yet</p>
            <p className="text-sm mb-5" style={{ color: 'var(--text-secondary)' }}>Start the conversation by creating the first post.</p>
            <button
              onClick={() => setShowNewForm(true)}
              className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 text-white text-sm font-bold rounded-xl hover:from-indigo-500 hover:to-violet-500 transition-all"
            >
              Create First Post
            </button>
          </div>
        )}

        {/* ── Posts List ── */}
        {!loading && !error && posts.length > 0 && (
          <div className="space-y-5">
            {posts.map((post, idx) => {
              const isExpanded = expanded[post.id];
              const preview = post.content?.length > 250 ? post.content.slice(0, 250) + '…' : post.content;

              return (
                <article
                  key={post.id || idx}
                  className="rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-xl"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                  }}
                >
                  {/* Post header */}
                  <div className="flex items-center gap-3 px-6 py-4 border-b" style={{ borderColor: 'var(--border)' }}>
                    <div
                      className="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-black text-white"
                      style={{ background: `hsl(${(post.username?.charCodeAt(0) || 0) * 20}, 65%, 50%)` }}
                    >
                      {(post.username || 'A').charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{post.username || 'Anonymous'}</span>
                      {post.problem && (
                        <span className="ml-2 text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                          {post.problem}
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] flex-shrink-0" style={{ color: 'var(--text-muted)' }}>{timeAgo(post.created_at)}</span>
                  </div>

                  {/* Post body */}
                  <div
                    className="px-6 py-5 cursor-pointer"
                    onClick={() => toggleExpand(post.id)}
                  >
                    <h2 className="text-base font-bold mb-2 hover:text-indigo-400 transition-colors" style={{ color: 'var(--text-primary)' }}>
                      {post.title}
                    </h2>
                    <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                      {isExpanded ? post.content : preview}
                    </p>
                    {post.content?.length > 250 && (
                      <button className="mt-2 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors">
                        {isExpanded ? 'Show less ↑' : 'Read more ↓'}
                      </button>
                    )}
                  </div>

                  {/* Comments section (when expanded) */}
                  {isExpanded && (
                    <div className="px-6 pb-4 space-y-1 border-t" style={{ borderColor: 'var(--border)', paddingTop: '12px' }}>
                      {post.comments && post.comments.length > 0 && (
                        <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
                          {post.comments.map((c, ci) => <CommentItem key={c.id || ci} comment={c} />)}
                        </div>
                      )}
                      {/* Comment input */}
                      <div className="flex gap-3 pt-4">
                        <input
                          type="text"
                          placeholder="Add a reply…"
                          value={commentInputs[post.id] || ''}
                          onChange={e => setCommentInputs(prev => ({ ...prev, [post.id]: e.target.value }))}
                          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleComment(post.id); } }}
                          className="flex-1 rounded-xl px-4 py-2.5 text-xs outline-none"
                          style={{ background: 'var(--bg-base)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
                        />
                        <button
                          onClick={() => handleComment(post.id)}
                          disabled={submittingComment[post.id] || !commentInputs[post.id]?.trim()}
                          className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white text-xs font-bold transition-colors"
                        >
                          {submittingComment[post.id] ? '…' : 'Reply'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Post footer */}
                  <div
                    className="flex items-center gap-4 px-6 py-3 border-t"
                    style={{ borderColor: 'var(--border)', background: 'var(--bg-surface)' }}
                  >
                    <button
                      onClick={() => handleUpvote(post.id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all active:scale-95 ${
                        upvoted[post.id]
                          ? 'bg-indigo-600 text-white'
                          : 'hover:bg-indigo-500/10 hover:text-indigo-400'
                      }`}
                      style={{ color: upvoted[post.id] ? undefined : 'var(--text-secondary)' }}
                    >
                      <svg className="w-3.5 h-3.5" fill={upvoted[post.id] ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                      </svg>
                      {post.upvotes || 0}
                    </button>

                    <button
                      onClick={() => toggleExpand(post.id)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all hover:text-indigo-400"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      {post.comments?.length || 0} {isExpanded ? 'Hide' : 'Replies'}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
