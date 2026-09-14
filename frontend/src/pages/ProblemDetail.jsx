import React, { useState, useEffect, useRef, useCallback, Suspense, lazy } from 'react';
import { toast } from 'react-hot-toast';
import { useParams, useNavigate } from 'react-router-dom';

const MonacoEditor = lazy(() => import('../components/MonacoEditor'));
import problemService from '../services/problemService';
import hintService from '../services/hintService';
import codeService from '../services/codeService';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const capitalizeFirst = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
};

export default function ProblemDetail({ user, theme }) {
  const { id } = useParams();
  const navigate = useNavigate();

  // Refs for resizable split pane
  const splitContainerRef = useRef(null);
  const isResizing = useRef(false);
  const isConsoleResizing = useRef(false);
  const editorPanelRef = useRef(null);

  // States
  const [problem, setProblem] = useState(null);
  const [code, setCode] = useState('');
  const [hints, setHints] = useState([]);
  const [loadingHint, setLoadingHint] = useState(false);
  const [loadingProblem, setLoadingProblem] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('description');
  const [leftWidth, setLeftWidth] = useState(() => Number(localStorage.getItem('hintcode_split_width')) || 33);
  const [language, setLanguage] = useState('javascript');
  const [editorCodes, setEditorCodes] = useState({});
  const monacoEditorRef = useRef(null);
  const [runResult, setRunResult] = useState(null);
  const [loadingRun, setLoadingRun] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTerminalOpen, setIsTerminalOpen] = useState(false);
  const [consoleHeight, setConsoleHeight] = useState(() => Number(localStorage.getItem('hintcode_console_height')) || 250);
  const [terminalTab, setTerminalTab] = useState('result');
  const [hintRatings, setHintRatings] = useState({});
  const [submissions, setSubmissions] = useState([]);
  const [hoverStar, setHoverStar] = useState({});
  const [isLeftPanelOpen, setIsLeftPanelOpen] = useState(true);
  const [customInput, setCustomInput] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [fontSize, setFontSize] = useState(() => Number(localStorage.getItem('hintcode_font_size')) || 13);
  const [discussPosts, setDiscussPosts] = useState([]);
  const [discussLoading, setDiscussLoading] = useState(false);
  const [newPostTitle, setNewPostTitle] = useState('');
  const [newPostContent, setNewPostContent] = useState('');
  const [isPostingDiscuss, setIsPostingDiscuss] = useState(false);
  const [showNewPostForm, setShowNewPostForm] = useState(false);

  useEffect(() => {
    localStorage.setItem('hintcode_split_width', leftWidth);
  }, [leftWidth]);

  useEffect(() => {
    localStorage.setItem('hintcode_console_height', consoleHeight);
  }, [consoleHeight]);

  useEffect(() => {
    localStorage.setItem('hintcode_font_size', fontSize);
  }, [fontSize]);

  useEffect(() => {
    const handleFullscreenChange = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(err => console.error(err));
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  useEffect(() => {
    loadProblemDetails();
    loadHistory();
  }, [id]);

  const loadDiscussPosts = async (problemDbId) => {
    if (!problemDbId) return;
    try {
      setDiscussLoading(true);
      const data = await apiClient.get(`/forums/?problem_id=${problemDbId}`);
      setDiscussPosts(Array.isArray(data) ? data : (data.results || []));
    } catch (e) {
      console.error('Failed to load discuss posts', e);
    } finally {
      setDiscussLoading(false);
    }
  };

  const handleSubmitDiscussPost = async () => {
    if (!newPostTitle.trim() || !newPostContent.trim()) return;
    try {
      setIsPostingDiscuss(true);
      await apiClient.post('/forums/', {
        title: newPostTitle.trim(),
        content: newPostContent.trim(),
        problem_id: problem?.id,
      });
      setNewPostTitle('');
      setNewPostContent('');
      setShowNewPostForm(false);
      loadDiscussPosts(problem?.id);
      toast.success('Post created!');
    } catch (e) {
      toast.error('Failed to create post.');
    } finally {
      setIsPostingDiscuss(false);
    }
  };

  useEffect(() => {
    if (!id || !language || !code) return;
    const timeoutId = setTimeout(() => {
      localStorage.setItem(`hintcode_autosave_${id}_${language}`, code);
    }, 1000);
    return () => clearTimeout(timeoutId);
  }, [code, language, id]);

  const loadHistory = async () => {
    try {
      if (!user) return;
      const data = await codeService.getHistory(user.id || 1, problem?.problem_id || problem?.id || id);
      setSubmissions(data);
    } catch (e) {
      console.error('Failed to load history', e);
    }
  };

  const loadProblemDetails = async () => {
    try {
      setLoadingProblem(true);
      const data = await problemService.getProblemById(id);
      setProblem(data);
      const defaultLang = data.language || 'javascript';
      setLanguage(defaultLang);
      const savedCode = localStorage.getItem(`hintcode_autosave_${id}_${defaultLang}`);
      const initialCode = savedCode || data.starting_code || getDefaultStartingCode(defaultLang, data.title);
      setCode(initialCode);
      setEditorCodes({ [defaultLang]: initialCode });
      setError(null);
    } catch (err) {
      console.error('Error fetching problem:', err);
      setError('Problem details could not be loaded.');
    } finally {
      setLoadingProblem(false);
    }
  };

  const getDefaultStartingCode = (lang, title) => {
    const fnName = title ? title.toLowerCase().replace(/[^a-zA-Z0-9]/g, '').slice(0, 30) : 'solve';
    const camelName = fnName.charAt(0).toLowerCase() + fnName.slice(1);
    const pascalName = fnName.charAt(0).toUpperCase() + fnName.slice(1);
    switch (lang) {
      case 'python':
        return `def ${camelName}():\n    # Write your solution here\n    pass\n\nif __name__ == '__main__':\n    # Read input and call ${camelName}()\n    pass`;
      case 'java':
        return `import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner scanner = new Scanner(System.in);\n        // Read input and print output\n    }\n}`;
      case 'cpp':
        return `#include <iostream>\n#include <vector>\nusing namespace std;\n\nint main() {\n    // Read input and print output\n    return 0;\n}`;
      case 'go':
        return `package main\n\nimport (\n\t"fmt"\n)\n\nfunc main() {\n\t// Read input and print output\n}`;
      case 'rust':
        return `use std::io;\n\nfn main() {\n    // Read input and print output\n}`;
      case 'typescript':
        return `import * as fs from 'fs';\n\nfunction main() {\n    const input = fs.readFileSync('/dev/stdin', 'utf-8');\n    // Parse input and print output\n}\n\nmain();`;
      case 'csharp':
        return `using System;\n\nclass Program {\n    static void Main(string[] args) {\n        // Read input and print output\n    }\n}`;
      case 'ruby':
        return `def solve\n  # Read input and print output\nend\n\nsolve()`;
      case 'kotlin':
        return `import java.util.Scanner\n\nfun main(args: Array<String>) {\n    val scanner = Scanner(System.` + `in` + `)\n    // Read input and print output\n}`;
      default: // javascript
        return `const fs = require('fs');\n\nfunction main() {\n    const input = fs.readFileSync(0, 'utf-8');\n    // Parse input and print output\n}\n\nmain();`;
    }
  };

  // Resize handler — using useCallback to avoid stale closure references
  const handleResize = useCallback((e) => {
    if (!isResizing.current || !splitContainerRef.current) return;
    const containerRect = splitContainerRef.current.getBoundingClientRect();
    const newWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
    if (newWidth > 20 && newWidth < 45) {
      setLeftWidth(newWidth);
    }
  }, []);

  const stopResize = useCallback(() => {
    isResizing.current = false;
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', stopResize);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }, [handleResize]);

  const startResize = useCallback((e) => {
    isResizing.current = true;
    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', stopResize);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [handleResize, stopResize]);

  // ── Console vertical resize handlers ──
  const handleConsoleResize = useCallback((e) => {
    if (!isConsoleResizing.current || !editorPanelRef.current) return;
    const panelRect = editorPanelRef.current.getBoundingClientRect();
    const newHeight = panelRect.bottom - e.clientY;
    if (newHeight > 40 && newHeight < panelRect.height * 0.7) {
      setConsoleHeight(newHeight);
    }
  }, []);

  const stopConsoleResize = useCallback(() => {
    isConsoleResizing.current = false;
    document.removeEventListener('mousemove', handleConsoleResize);
    document.removeEventListener('mouseup', stopConsoleResize);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }, [handleConsoleResize]);

  const startConsoleResize = useCallback((e) => {
    e.preventDefault();
    isConsoleResizing.current = true;
    document.addEventListener('mousemove', handleConsoleResize);
    document.addEventListener('mouseup', stopConsoleResize);
    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';
  }, [handleConsoleResize, stopConsoleResize]);

  // Handle language updates with template caching
  const handleLanguageChange = (newLang) => {
    // Cache current code
    setEditorCodes(prev => ({
      ...prev,
      [language]: code
    }));
    
    setLanguage(newLang);
    
    // Retrieve cached code or load default template
    if (editorCodes[newLang]) {
      setCode(editorCodes[newLang]);
    } else {
      const savedCode = localStorage.getItem(`hintcode_autosave_${id}_${newLang}`);
      const template = savedCode || getDefaultStartingCode(newLang, problem?.title);
      setCode(template);
      setEditorCodes(prev => ({
        ...prev,
        [newLang]: template
      }));
    }
  };

  // Reset editor template
  const handleResetCode = () => {
    if (window.confirm("Reset editor to default code template? Any changes will be lost.")) {
      const template = getDefaultStartingCode(language, problem?.title);
      setCode(template);
      setEditorCodes(prev => ({
        ...prev,
        [language]: template
      }));
      localStorage.removeItem(`hintcode_autosave_${id}_${language}`);
    }
  };

  // Hint requesting
  const requestHint = async () => {
    if (!user || !problem) return;
    setActiveTab('hints');
    try {
      setLoadingHint(true);
      const result = await hintService.requestHint(
        user?.id || 1,
        problem.problem_id || problem.id,
        code,
        {
          title: problem.title,
          description: problem.description
        }
      );
      
      if (result && result.hint) {
        setHints(prev => [result.hint, ...prev]);
        toast.success("AI Hint generated successfully!");
      }
    } catch (err) {
      console.error(err);
      if (err?.response?.status === 429) {
        toast.error("Too many requests! Please wait a few minutes before asking for another hint.", { duration: 4000 });
      } else {
        toast.error("Failed to generate hint. Please try again.");
      }
    } finally {
      setLoadingHint(false);
    }
  };

  // Submit Feedback on Hints
  const handleRateHint = async (hintDeliveryId, rating) => {
    try {
      await hintService.provideFeedback(hintDeliveryId, `Rated ${rating} stars`, rating);
      setHintRatings(prev => ({
        ...prev,
        [hintDeliveryId]: rating
      }));
    } catch (err) {
      console.error(err);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard!", { style: { fontSize: '12px' } });
  };

  // Code runs
  const runCode = useCallback(async () => {
    if (!user || !problem) return;
    setIsTerminalOpen(true);
    setTerminalTab('result');
    try {
      setLoadingRun(true);
      setRunResult(null);
      const result = await codeService.runCode(
        user?.id || 1,
        problem.problem_id || problem.id,
        code,
        language,
        customInput
      );
      setRunResult(result);
      loadHistory();
      
      if (result.success) {
        const solvedList = JSON.parse(localStorage.getItem('solvedProblems') || '[]');
        if (!solvedList.includes(problem.problem_id)) {
          solvedList.push(problem.problem_id);
          localStorage.setItem('solvedProblems', JSON.stringify(solvedList));
        }
      } else {
        // Failed run: check for auto-trigger
        try {
          const autoCheck = await hintService.checkAutoTrigger(
            user?.id || 1,
            problem?.problem_id || problem?.id || 1,
            code || '\n',
            { title: problem.title, description: problem.description }
          );
          if (autoCheck?.should_trigger && autoCheck.hint) {
            setHints(prev => [autoCheck.hint, ...prev]);
            toast("You seem stuck! The AI generated a hint for you.", {
              icon: '💡',
              style: { borderRadius: '10px', background: '#333', color: '#fff' }
            });
            setActiveTab('hints');
          }
        } catch (e) {
          console.error("Auto-trigger error", e);
        }
      }
    } catch (err) {
      console.error(err);
      setRunResult({
        success: false,
        errors: [{ message: err.message || 'Execution error.' }]
      });
    } finally {
      setLoadingRun(false);
    }
  }, [user, problem, code, language, customInput]);

  const submitSolution = useCallback(async () => {
    if (!user || !problem) return;
    setIsTerminalOpen(true);
    setTerminalTab('result');
    try {
      setIsSubmitting(true);
      const result = await codeService.submitSolution(
        user?.id || 1,
        problem?.problem_id || problem?.id || 1,
        code || '\n',
        language
      );
      setRunResult({
        ...result,
        isSubmission: true
      });
      loadHistory();
      
      if (result.success) {
        const solvedList = JSON.parse(localStorage.getItem('solvedProblems') || '[]');
        if (!solvedList.includes(problem.problem_id)) {
          solvedList.push(problem.problem_id);
          localStorage.setItem('solvedProblems', JSON.stringify(solvedList));
        }
      } else {
        // Failed submit: check for auto-trigger
        try {
          const autoCheck = await hintService.checkAutoTrigger(
            user?.id || 1,
            problem?.problem_id || problem?.id || 1,
            code || '\n',
            { title: problem.title, description: problem.description }
          );
          if (autoCheck?.should_trigger && autoCheck.hint) {
            setHints(prev => [autoCheck.hint, ...prev]);
            toast("You seem stuck! The AI generated a hint for you.", {
              icon: '💡',
              style: { borderRadius: '10px', background: '#333', color: '#fff' }
            });
            setActiveTab('hints');
          }
        } catch (e) {
          console.error("Auto-trigger error", e);
        }
      }
    } catch (err) {
      console.error(err);
      setRunResult({
        success: false,
        errors: [{ message: err.message || 'Submission failed.' }],
        isSubmission: true
      });
    } finally {
      setIsSubmitting(false);
    }
  }, [user, problem, code, language]);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+Enter or Cmd+Enter to Run Code
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (e.shiftKey) {
          submitSolution();
        } else {
          runCode();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [runCode, submitSolution]);

  // Custom Markdown Parser with advanced example extraction
  const parseMarkdown = (md) => {
    if (!md) return '';
    let html = md
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Fenced Code blocks
    html = html.replace(/```([\s\S]*?)```/g, (match, body) => {
      return `<pre class="bg-slate-950 border border-[var(--border)] rounded-xl p-5 my-4 overflow-x-auto font-mono text-xs text-[#818cf8]"><code>${body.trim()}</code></pre>`;
    });

    // Inline code tags
    html = html.replace(/`([^`]+)`/g, '<code class="bg-[#161b22]/80 border border-[#21262d] text-indigo-300 rounded px-1.5 py-0.5 font-mono text-xs">$1</code>');

    // Bold text
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-bold text-slate-100">$1</strong>');

    // Headings
    html = html.replace(/^##\s+(.+)$/gm, '<h2 class="text-xs font-bold text-white uppercase tracking-wider mt-6 mb-3 border-b border-[#21262d] pb-2 flex items-center gap-2">$1</h2>');
    html = html.replace(/^###\s+(.+)$/gm, '<h3 class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mt-4 mb-2">$1</h3>');
    html = html.replace(/^#\s+(.+)$/gm, '<h1 class="text-lg font-black text-white mt-6 mb-4">$1</h1>');

    // Bullet points
    html = html.replace(/^\s*-\s+(.+)$/gm, '<li class="text-slate-400 ml-5 list-disc my-1.5">$1</li>');

    // Example Extraction Block
    const lines = html.split('\n');
    let outputLines = [];
    let inExampleBlock = false;
    let exampleBlockBuffer = [];

    for (let line of lines) {
      const trimmed = line.trim();
      
      // Match example markers e.g. **Example 1:**
      if (trimmed.toLowerCase().includes('example') && (trimmed.startsWith('<strong') || trimmed.endsWith(':') || trimmed.includes('strong>'))) {
        if (inExampleBlock) {
          outputLines.push(flushExampleBlock(exampleBlockBuffer));
          exampleBlockBuffer = [];
        }
        inExampleBlock = true;
        const cleanHeader = trimmed.replace(/<\/?strong>/g, '').replace(/:$/, '').trim();
        outputLines.push(`<div class="text-xs font-black text-white uppercase tracking-wider mt-6 mb-2.5 flex items-center gap-1.5"><span class="w-1.5 h-1.5 rounded-full bg-indigo-500 shadow-[0_0_5px_#6366f1]"></span>${cleanHeader}</div>`);
        continue;
      }
      
      if (inExampleBlock) {
        if (trimmed.includes('Input:') || trimmed.includes('Output:') || trimmed.includes('Explanation:') || trimmed.startsWith('Input') || trimmed.startsWith('Output')) {
          exampleBlockBuffer.push(line);
          continue;
        } else if (trimmed === '' || trimmed === '<br />') {
          continue;
        } else {
          outputLines.push(flushExampleBlock(exampleBlockBuffer));
          exampleBlockBuffer = [];
          inExampleBlock = false;
        }
      }
      
      outputLines.push(line);
    }
    
    if (inExampleBlock && exampleBlockBuffer.length > 0) {
      outputLines.push(flushExampleBlock(exampleBlockBuffer));
    }

    let finalHtml = outputLines.map(line => {
      const t = line.trim();
      if (t === '' || t === '<br />') return '';
      if (t.startsWith('<h') || t.startsWith('<li') || t.startsWith('<pre') || t.startsWith('</pre') || t.startsWith('<div') || t.startsWith('</div')) {
        return line;
      }
      return `<p class="my-2 text-slate-300 leading-relaxed">${line}</p>`;
    }).join('\n');

    return finalHtml;
  };

  const flushExampleBlock = (buffer) => {
    let inputStr = '';
    let outputStr = '';
    let explanationStr = '';
    
    buffer.forEach(line => {
      let clean = line.replace(/<\/?strong>/g, '').replace(/<br\s*\/?>/gi, '').trim();
      
      if (clean.startsWith('Input:') || clean.includes('Input:')) {
        inputStr = clean.split('Input:')[1]?.trim() || '';
      } else if (clean.startsWith('Output:') || clean.includes('Output:')) {
        outputStr = clean.split('Output:')[1]?.trim() || '';
      } else if (clean.startsWith('Explanation:') || clean.includes('Explanation:')) {
        explanationStr = clean.split('Explanation:')[1]?.trim() || '';
      } else {
        if (explanationStr) {
          explanationStr += ' ' + clean;
        } else if (outputStr) {
          outputStr += ' ' + clean;
        } else if (inputStr) {
          inputStr += ' ' + clean;
        }
      }
    });

    if (!inputStr && !outputStr && !explanationStr) {
      return buffer.join('<br />');
    }

    return `
<div class="bg-[var(--bg-surface)]/50 border border-[var(--border)] rounded-2xl p-5 my-4 font-sans text-xs space-y-3 shadow-inner">
  ${inputStr ? `<div><span class="text-slate-500 font-bold uppercase tracking-wider text-[9px] block mb-1">Input</span><pre class="bg-[var(--bg-base)] border border-[var(--border)] p-2.5 rounded-xl font-mono text-slate-200 overflow-x-auto leading-relaxed">${inputStr}</pre></div>` : ''}
  ${outputStr ? `<div><span class="text-slate-500 font-bold uppercase tracking-wider text-[9px] block mb-1">Output</span><pre class="bg-[var(--bg-base)] border border-[var(--border)] p-2.5 rounded-xl font-mono text-indigo-300 overflow-x-auto font-bold leading-relaxed">${outputStr}</pre></div>` : ''}
  ${explanationStr ? `<div class="pt-2 border-t border-[var(--border)]" ><span class="text-slate-500 font-bold uppercase tracking-wider text-[9px] block mb-1">Explanation</span><p class="text-slate-400 leading-relaxed pl-0.5">${explanationStr}</p></div>` : ''}
</div>`;
  };

  const getDifficultyColor = (diff) => {
    switch (diff?.toLowerCase()) {
      case 'easy': return 'bg-green-500/10 text-green-400 border border-green-500/20';
      case 'medium': return 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20';
      case 'hard': return 'bg-red-500/10 text-red-400 border border-red-500/20';
      default: return 'bg-slate-800 text-slate-400 border-[#21262d]';
    }
  };

  // capitalizeFirst is now a module-level utility function defined above

  if (loadingProblem) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[var(--bg-base)]">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-500 mx-auto"></div>
          <p className="text-[#8b949e] text-xs font-semibold tracking-widest uppercase">Loading workspace...</p>
        </div>
      </div>
    );
  }

  if (error || !problem) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[var(--bg-base)] text-center p-6 space-y-4">
        <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" strokeWidth={2} />
          <line x1="12" y1="8" x2="12" y2="12" strokeWidth={2} />
          <line x1="12" y1="16" x2="12.01" y2="16" strokeWidth={2.5} />
        </svg>
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">Loading failed</h2>
        <p className="text-[#8b949e] max-w-sm text-xs">{error || "This problem could not be loaded."}</p>
        <button onClick={() => navigate('/')} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-[#21262d] rounded-xl text-xs font-bold uppercase tracking-wider transition-colors">
          Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-[var(--bg-base)] h-full min-h-0 overflow-hidden" ref={splitContainerRef}>
      
      {/* Workspace Header */}
      <div className="bg-[var(--bg-surface)]/80 border-b border-[var(--border)] px-4 py-2.5 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="p-1.5 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-slate-800/60 transition-colors focus:outline-none focus:ring-1 focus:ring-indigo-500/30"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          {/* Sidebar Toggle */}
          <button
            onClick={() => setIsLeftPanelOpen(prev => !prev)}
            className={`p-1.5 rounded-lg transition-all duration-200 focus:outline-none focus:ring-1 focus:ring-indigo-500/30 ${
              isLeftPanelOpen
                ? 'text-indigo-400 bg-indigo-500/10 hover:bg-indigo-500/20'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-slate-800/60'
            }`}
            title={isLeftPanelOpen ? 'Hide description panel' : 'Show description panel'}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
            </svg>
          </button>
          <span className="text-[10px] font-bold text-[#8b949e] uppercase tracking-widest">Workspace</span>
          <span className="text-slate-600 font-medium">/</span>
          <h2 className="text-sm font-bold text-[var(--text-primary)] truncate max-w-[200px] sm:max-w-[400px]">
            {problem.title}
          </h2>
        </div>

        <div className="flex items-center gap-3 select-none">
          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${getDifficultyColor(problem.difficulty)}`}>
            {capitalizeFirst(problem.difficulty)}
          </span>
          <span className="bg-indigo-500/10 border border-indigo-500/25 text-indigo-400 text-[10px] font-bold px-2.5 py-0.5 rounded-full">
            {problem.topic}
          </span>
        </div>
      </div>

      {/* Main Split Panels */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden relative min-h-0">
        
        {/* Left Description Column — Collapsible */}
        <div 
          className={`flex flex-col min-h-0 bg-[var(--bg-surface)]/15 border-r border-[var(--border)] overflow-hidden transition-all duration-300 ease-in-out ${
            isLeftPanelOpen ? '' : 'w-0 min-w-0 border-r-0'
          }`}
          style={isLeftPanelOpen ? { width: `${leftWidth}%`, flexShrink: 0 } : { width: 0 }}
        >
          {/* Tabs bar */}
          <div className="flex bg-[var(--bg-surface)]/50 border-b border-[var(--border)] px-4 flex-shrink-0 select-none">
            <button
              onClick={() => setActiveTab('description')}
              className={`px-3 py-3 border-b-2 text-[10px] font-bold uppercase tracking-widest transition-all focus:outline-none ${
                activeTab === 'description'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-[#8b949e] hover:text-[#f0f6fc]'
              }`}
            >
              Description
            </button>
            <button
              onClick={() => setActiveTab('hints')}
              className={`px-3 py-3 border-b-2 text-[10px] font-bold uppercase tracking-widest transition-all focus:outline-none flex items-center gap-1.5 ${
                activeTab === 'hints'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-[#8b949e] hover:text-[#f0f6fc]'
              }`}
            >
              Hints
              {hints.length > 0 && (
                <span className="w-5 h-5 bg-indigo-500/20 text-indigo-400 border border-indigo-500/40 rounded-full flex items-center justify-center text-[9px] font-bold">
                  {hints.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('submissions')}
              className={`px-3 py-3 border-b-2 text-[10px] font-bold uppercase tracking-widest transition-all focus:outline-none flex items-center gap-1.5 ${
                activeTab === 'submissions'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-[#8b949e] hover:text-[#f0f6fc]'
              }`}
            >
              History
              {submissions.length > 0 && (
                <div className="ml-1.5 flex items-center justify-center bg-[var(--bg-surface)] text-[var(--text-secondary)] text-[10px] font-bold px-1.5 py-0.5 rounded-md">
                  {submissions.length}
                </div>
              )}
            </button>
            <button
              onClick={() => { setActiveTab('discuss'); if (problem?.id) loadDiscussPosts(problem.id); }}
              className={`px-3 py-3 border-b-2 text-[10px] font-bold uppercase tracking-widest transition-all focus:outline-none flex items-center gap-1.5 ${
                activeTab === 'discuss'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-[#8b949e] hover:text-[#f0f6fc]'
              }`}
            >
              Discuss
              {discussPosts.length > 0 && (
                <div className="ml-1.5 flex items-center justify-center bg-[var(--bg-surface)] text-[var(--text-secondary)] text-[10px] font-bold px-1.5 py-0.5 rounded-md">
                  {discussPosts.length}
                </div>
              )}
            </button>
          </div>

          {/* Scroll Content Area */}
          <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-4 space-y-4 scrollbar-thin">
            
            {activeTab === 'description' && (
              <div className="prose prose-invert max-w-none text-[#8b949e] text-xs leading-relaxed space-y-4">
                {problem.description ? (
                  <div dangerouslySetInnerHTML={{ __html: parseMarkdown(problem.description) }} />
                ) : (
                  <p>No description loaded.</p>
                )}
              </div>
            )}

            {activeTab === 'hints' && (
              <div className="space-y-4">
                {/* Request Hint banner */}
                <div className="bg-[var(--bg-surface)]/60 border border-[var(--border)] p-5 rounded-2xl text-center space-y-4 shadow-xl">
                  <div className="w-10 h-10 bg-indigo-500/10 rounded-full border border-indigo-500/30 flex items-center justify-center text-indigo-400 mx-auto shadow-md shadow-indigo-500/5">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider">Progressive Assist</h3>
                    <p className="text-[11px] text-[#8b949e] max-w-xs mx-auto">Generate hint cards suited to your current evaluation. No spoiler code blocks.</p>
                  </div>
                  <button
                    onClick={requestHint}
                    disabled={loadingHint}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-[10px] font-bold uppercase tracking-wider rounded-xl transition-all shadow-lg shadow-indigo-500/10 disabled:opacity-50 active:scale-[0.98] inline-flex items-center gap-2"
                  >
                    {loadingHint ? (
                      <>
                        <div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white"></div>
                        <span>Evaluating...</span>
                      </>
                    ) : (
                      <span>Request Hint</span>
                    )}
                  </button>
                </div>

                {/* Hints progressive reveal timeline */}
                <div className="space-y-4 pt-2">
                  {hints.map((hint, idx) => {
                    const levelLabel = hint.level === 1 ? 'Conceptual' : hint.level === 2 ? 'Approach' : 'Implementation';
                    const rating = hintRatings[hint.id];
                    const activeHoverStar = hoverStar[hint.id] || 0;
                    return (
                      <div 
                        key={idx} 
                        className="bg-[var(--bg-surface)]/40 border border-[var(--border)] rounded-2xl p-5 space-y-3.5 animate-fade-in shadow-sm"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[9px] font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20 uppercase tracking-widest">
                            Lvl {hint.level}: {levelLabel}
                          </span>
                          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                            {hint.timestamp ? new Date(hint.timestamp).toLocaleTimeString() : 'Just now'}
                          </span>
                        </div>
                        
                        <div className="text-slate-300 text-xs leading-relaxed overflow-x-auto hint-markdown-content">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              code({node, inline, className, children, ...props}) {
                                const match = /language-(\w+)/.exec(className || '')
                                return !inline && match ? (
                                  <SyntaxHighlighter
                                    {...props}
                                    children={String(children).replace(/\n$/, '')}
                                    style={vscDarkPlus}
                                    language={match[1]}
                                    PreTag="div"
                                    className="rounded-md my-2 text-[11px]"
                                  />
                                ) : (
                                  <code {...props} className="bg-slate-800 text-indigo-300 px-1 py-0.5 rounded text-[10px] font-mono">
                                    {children}
                                  </code>
                                )
                              }
                            }}
                          >
                            {hint.content}
                          </ReactMarkdown>
                        </div>

                        {/* Feedback Rating Block with glowing stars */}
                        <div className="pt-3.5 border-t border-[#21262d]/50 flex items-center justify-between text-xs text-slate-400 select-none">
                          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wide">Helpful?</span>
                          <div className="flex items-center gap-1.5">
                            {rating ? (
                              <span className="text-indigo-400 font-bold text-[9px] bg-indigo-500/5 px-2.5 py-0.5 rounded border border-indigo-500/10 uppercase tracking-wider">
                                Rated {rating} / 5
                              </span>
                            ) : (
                              [1, 2, 3, 4, 5].map((starVal) => {
                                const isHighlighted = starVal <= (activeHoverStar || 0);
                                return (
                                  <button
                                    key={starVal}
                                    onMouseEnter={() => setHoverStar(prev => ({ ...prev, [hint.id]: starVal }))}
                                    onMouseLeave={() => setHoverStar(prev => ({ ...prev, [hint.id]: 0 }))}
                                    onClick={() => handleRateHint(hint.id, starVal)}
                                    className={`p-0.5 rounded transition-all focus:outline-none focus:ring-1 focus:ring-amber-400/30 ${
                                      isHighlighted ? 'text-amber-400 scale-110' : 'text-slate-600 hover:text-amber-400'
                                    }`}
                                  >
                                    <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                    </svg>
                                  </button>
                                );
                              })
                            )}
                          </div>
                        </div>

                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {activeTab === 'submissions' && (
              <div className="flex-1 overflow-auto p-4 md:p-6 pb-20 custom-scrollbar">
              <div className="space-y-4 max-w-3xl mx-auto">
                {submissions.length === 0 ? (
                  <div className="text-center py-16 px-4 bg-[var(--bg-surface)]/30 rounded-2xl border border-[var(--border)]">
                    <svg className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <h3 className="text-sm font-bold text-[var(--text-primary)] mb-1">No Submissions Yet</h3>
                    <p className="text-[11px] text-[var(--text-secondary)] max-w-xs mx-auto">
                      Your code submissions and execution history will appear here.
                    </p>
                  </div>
                ) : (
                  submissions.map((sub, idx) => (
                    <div key={sub.id || idx} className="bg-[var(--bg-surface)] border border-[var(--border)] p-4 rounded-xl shadow-sm hover:border-[var(--border-hover)] transition-colors group">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-black tracking-wide uppercase ${
                            sub.status === 'success' ? 'bg-green-500/10 text-green-500 border border-green-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'
                          }`}>
                            {sub.status === 'success' ? 'Accepted' : 'Runtime Error'}
                          </span>
                          <span className="text-xs font-mono text-[var(--text-secondary)] opacity-80">
                            {new Date(sub.created_at).toLocaleDateString()} {new Date(sub.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono text-[var(--text-muted)] bg-[var(--bg-base)] px-2 py-1 rounded-md border border-[var(--border)]">
                            {sub.language}
                          </span>
                          <span className="text-[10px] font-mono text-[var(--text-muted)] bg-[var(--bg-base)] px-2 py-1 rounded-md border border-[var(--border)] flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            {sub.execution_time || '0.0s'}
                          </span>
                        </div>
                      </div>
                      <div className="relative mt-2">
                        <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                          <button
                            onClick={() => {
                              setCode(sub.code);
                              setEditorCodes(prev => ({ ...prev, [sub.language]: sub.code }));
                              setLanguage(sub.language);
                              setActiveTab('description');
                            }}
                            className="bg-indigo-500 hover:bg-indigo-600 text-white p-1.5 rounded-lg shadow-lg transition-colors flex items-center gap-1.5 px-3"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" /></svg>
                            <span className="text-[10px] font-bold">Restore</span>
                          </button>
                        </div>
                        <pre className="text-[10px] font-mono bg-[var(--bg-base)] p-3 rounded-lg text-[var(--text-primary)] overflow-x-auto max-h-32 border border-[var(--border)]/50">
                          {sub.code}
                        </pre>
                      </div>
                    </div>
                  ))
                )}
              </div>
              </div>
            )}

            {activeTab === 'discuss' && (
              <div className="space-y-4">
                {/* New Post Toggle */}
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-widest">Discussion</h3>
                  <button
                    onClick={() => setShowNewPostForm(p => !p)}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-[10px] font-bold rounded-lg transition-colors"
                  >
                    {showNewPostForm ? 'Cancel' : '+ New Post'}
                  </button>
                </div>

                {showNewPostForm && (
                  <div className="bg-[var(--bg-surface)]/60 border border-[var(--border)] rounded-xl p-4 space-y-3">
                    <input
                      type="text"
                      placeholder="Post title..."
                      value={newPostTitle}
                      onChange={e => setNewPostTitle(e.target.value)}
                      className="w-full bg-[var(--bg-base)] border border-[var(--border)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] placeholder-slate-500 focus:outline-none focus:border-indigo-500/50"
                    />
                    <textarea
                      placeholder="Share your thoughts, questions, or approach..."
                      value={newPostContent}
                      onChange={e => setNewPostContent(e.target.value)}
                      rows={4}
                      className="w-full bg-[var(--bg-base)] border border-[var(--border)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 resize-none"
                    />
                    <button
                      onClick={handleSubmitDiscussPost}
                      disabled={isPostingDiscuss || !newPostTitle.trim() || !newPostContent.trim()}
                      className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-[10px] font-bold rounded-lg transition-colors"
                    >
                      {isPostingDiscuss ? 'Posting...' : 'Submit Post'}
                    </button>
                  </div>
                )}

                {discussLoading ? (
                  <div className="flex justify-center py-8">
                    <div className="w-6 h-6 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
                  </div>
                ) : discussPosts.length === 0 ? (
                  <div className="text-center py-10 text-[var(--text-secondary)] text-xs">
                    <svg className="w-8 h-8 mx-auto mb-2 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    No discussions yet. Be the first to post!
                  </div>
                ) : (
                  <div className="space-y-3">
                    {discussPosts.map(post => (
                      <div key={post.id} className="bg-[var(--bg-surface)]/40 border border-[var(--border)] rounded-xl p-4 space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <h4 className="text-xs font-bold text-[var(--text-primary)] leading-snug">{post.title}</h4>
                          <span className="text-[9px] text-slate-500 flex-shrink-0">{post.username}</span>
                        </div>
                        <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed line-clamp-3">{post.content}</p>
                        <div className="flex items-center gap-3 pt-1 text-[10px] text-slate-500">
                          <span>👍 {post.upvotes}</span>
                          <span>💬 {post.comments?.length || 0} replies</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Panel Dragger Handle — hidden when sidebar collapsed */}
        <div 
          className="hidden md:flex w-[12px] hover:w-[16px] cursor-col-resize select-none bg-[var(--bg-base)] border-x border-[var(--border)]/50 z-20 transition-all items-center justify-center group relative"
          onMouseDown={isLeftPanelOpen ? startResize : undefined}
        >
          {isLeftPanelOpen ? (
            <div className="w-[2px] h-8 bg-slate-700 rounded-full group-hover:bg-indigo-500 group-hover:h-12 group-hover:shadow-[0_0_8px_#6366f1] transition-all duration-300" />
          ) : (
            <div className="w-[2px] h-full bg-indigo-500/30 group-hover:bg-indigo-500 transition-all duration-300" />
          )}

          {/* Toggle Button embedded in the dragger */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsLeftPanelOpen(!isLeftPanelOpen);
            }}
            className="absolute top-1/2 -translate-y-1/2 -left-[14px] bg-[var(--bg-surface)] border border-[var(--border)] text-slate-400 hover:text-indigo-400 p-1 rounded-l-md rounded-r-none shadow-md z-30 focus:outline-none opacity-0 group-hover:opacity-100 transition-opacity"
            title={isLeftPanelOpen ? 'Collapse Panel' : 'Expand Panel'}
          >
            <svg className={`w-3.5 h-3.5 transition-transform ${isLeftPanelOpen ? '' : 'rotate-180'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>

        {/* Right Editor Column */}
        <div className="flex-1 flex flex-col overflow-hidden bg-[var(--bg-base)]" ref={editorPanelRef}>
          
          {/* Monaco Editor Toolbar */}
          <div className="bg-[var(--bg-surface)]/45 border-b border-[var(--border)] px-4 py-2 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-3 select-none">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Compiler</span>
              <select
                className="px-2.5 py-1 bg-[var(--bg-base)] border border-[var(--border)] rounded-lg text-[10px] font-bold text-slate-400 focus:outline-none focus:border-indigo-500/40 cursor-pointer uppercase"
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value)}
              >
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
                <option value="python">Python</option>
                <option value="java">Java</option>
                <option value="cpp">C++</option>
                <option value="go">Go</option>
                <option value="rust">Rust</option>
                <option value="csharp">C#</option>
                <option value="kotlin">Kotlin</option>
                <option value="ruby">Ruby</option>
              </select>

              {/* Font Size Slider */}
              <div className="flex items-center gap-2 mr-2 border-r border-[var(--border)] pr-4">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest hidden lg:block">Size</span>
                <input 
                  type="range" 
                  min="10" max="24" 
                  value={fontSize} 
                  onChange={(e) => setFontSize(Number(e.target.value))}
                  className="w-16 h-1 bg-[var(--bg-base)] rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  title={`Font Size: ${fontSize}px`}
                />
              </div>

              {/* Format Code button */}
              <button
                onClick={() => monacoEditorRef.current?.formatDocument()}
                className="p-1 rounded hover:bg-[#161b22] text-slate-500 hover:text-indigo-400 transition-colors focus:outline-none ml-1"
                title="Format document"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
                </svg>
              </button>

              {/* Reset Code template button */}
              <button
                onClick={handleResetCode}
                className="p-1 rounded hover:bg-[#161b22] text-slate-500 hover:text-red-400 transition-colors focus:outline-none"
                title="Reset boilerplate template"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                </svg>
              </button>
            </div>

            <div className="flex gap-2">
              {/* ─── Fullscreen Button ─── */}
              <button
                onClick={toggleFullscreen}
                className="group relative px-3 py-1.5 rounded-xl text-[10px] font-bold uppercase tracking-wider transition-all duration-200 inline-flex items-center gap-1.5 focus:outline-none focus:ring-1 focus:ring-slate-500/30 bg-[var(--bg-surface)] hover:bg-[#161b22] text-[var(--text-secondary)] hover:text-slate-200 border border-[var(--border)] hover:border-slate-600"
                title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
              >
                {isFullscreen ? (
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 6H5v4m10-4h4v4M9 18H5v-4m10 4h4v-4" /></svg>
                ) : (
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
                )}
              </button>

              {/* ─── Run Button ─── */}
              <button
                onClick={runCode}
                disabled={loadingRun || isSubmitting}
                className={`group relative px-4 py-1.5 rounded-xl text-[10px] font-bold uppercase tracking-wider transition-all duration-200 inline-flex items-center gap-2 focus:outline-none focus:ring-1 focus:ring-emerald-500/30 ${
                  loadingRun
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-sm shadow-emerald-500/10'
                    : 'bg-[var(--bg-surface)] hover:bg-emerald-500/10 text-[var(--text-secondary)] hover:text-emerald-400 border border-[var(--border)] hover:border-emerald-500/30'
                } disabled:opacity-40`}
              >
                {loadingRun ? (
                  <>
                    <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth={4} />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <span>Running...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-3 h-3 transition-transform group-hover:scale-110" fill="currentColor" viewBox="0 0 24 24">
                      <polygon points="5 3 19 12 5 21 5 3" />
                    </svg>
                    <span>Run</span>
                  </>
                )}
              </button>
              
              {/* ─── Submit Button ─── */}
              <button
                onClick={submitSolution}
                disabled={loadingRun || isSubmitting}
                className={`group relative px-4 py-1.5 rounded-xl text-[10px] font-bold uppercase tracking-wider transition-all duration-200 inline-flex items-center gap-2 focus:outline-none disabled:opacity-40 ${
                  isSubmitting
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-700 text-white shadow-lg shadow-indigo-500/25 animate-pulse'
                    : 'bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-md shadow-indigo-500/10 hover:shadow-indigo-500/25 active:scale-[0.97]'
                } focus:ring-1 focus:ring-indigo-400/40`}
              >
                {isSubmitting ? (
                  <>
                    <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth={4} />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <span>Submitting...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-3 h-3 transition-transform group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Submit</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Monaco wrapper */}
          <div className="flex-1 min-h-0 bg-[var(--bg-base)]">
            <Suspense fallback={
              <div className="h-full w-full flex items-center justify-center text-[var(--text-muted)] bg-[var(--bg-base)]">
                <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            }>
              <MonacoEditor
                ref={monacoEditorRef}
                value={code}
                onChange={setCode}
                language={language}
                theme={theme}
                fontSize={fontSize}
              />
            </Suspense>
          </div>

          {/* Terminal / Console — draggable height */}
          <div 
            className="border-t border-[var(--border)] bg-[var(--bg-base)] flex flex-col"
            style={{ height: isTerminalOpen ? `${consoleHeight}px` : '40px', flexShrink: 0 }}
          >
            {/* Console drag handle — only when open */}
            {isTerminalOpen && (
              <div
                onMouseDown={startConsoleResize}
                className="h-[5px] cursor-row-resize bg-[var(--bg-base)] hover:bg-indigo-500/20 transition-colors flex items-center justify-center group flex-shrink-0"
              >
                <div className="w-10 h-[3px] bg-slate-700/60 rounded-full group-hover:bg-indigo-500 group-hover:shadow-[0_0_6px_#6366f1] transition-all" />
              </div>
            )}
            {/* Terminal toggle bar */}
            <div className="bg-[var(--bg-surface)]/45 border-b border-[var(--border)]/25 flex items-center justify-between flex-shrink-0 select-none">
              <div 
                onClick={() => setIsTerminalOpen(!isTerminalOpen)}
                className="px-4 py-2.5 flex items-center gap-2 cursor-pointer text-[10px] font-bold text-slate-500 uppercase tracking-widest hover:bg-slate-900/10 flex-1"
              >
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                <span>Console</span>
              </div>
              
              {isTerminalOpen && (
                <div className="flex pr-2 gap-1.5">
                  <button
                    onClick={() => setTerminalTab('testcase')}
                    className={`px-3 py-1.5 text-[9px] font-bold uppercase rounded-lg transition-colors focus:outline-none ${
                      terminalTab === 'testcase'
                        ? 'bg-slate-800 text-indigo-400 border border-slate-700'
                        : 'text-slate-500 hover:text-slate-400'
                    }`}
                  >
                    Testcase
                  </button>
                  <button
                    onClick={() => setTerminalTab('result')}
                    className={`px-3 py-1.5 text-[9px] font-bold uppercase rounded-lg transition-colors focus:outline-none ${
                      terminalTab === 'result'
                        ? 'bg-slate-800 text-indigo-400 border border-slate-700'
                        : 'text-slate-500 hover:text-slate-400'
                    }`}
                  >
                    Result
                  </button>
                  <button
                    onClick={() => setTerminalTab('custom_input')}
                    className={`px-3 py-1.5 text-[9px] font-bold uppercase rounded-lg transition-colors focus:outline-none ${
                      terminalTab === 'custom_input'
                        ? 'bg-slate-800 text-indigo-400 border border-slate-700'
                        : 'text-slate-500 hover:text-slate-400'
                    }`}
                  >
                    Custom Input
                  </button>
                </div>
              )}
              
              <div 
                onClick={() => setIsTerminalOpen(!isTerminalOpen)}
                className="px-4 py-2.5 cursor-pointer text-slate-500 hover:text-slate-300"
              >
                <svg className={`w-3.5 h-3.5 transition-transform ${isTerminalOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            {/* Terminal Body */}
            {isTerminalOpen && (
              <div className="flex-1 overflow-auto p-5 font-mono text-xs text-slate-400">
                
                {terminalTab === 'custom_input' && (
                  <div className="space-y-4 h-full flex flex-col">
                    <span className="text-slate-500 font-bold uppercase tracking-wider text-[9px] block">Standard Input (stdin)</span>
                    <textarea
                      value={customInput}
                      onChange={(e) => setCustomInput(e.target.value)}
                      placeholder="Enter custom input here..."
                      className="flex-1 bg-[var(--bg-surface)]/60 border border-[var(--border)] p-3.5 rounded-xl font-mono text-slate-200 text-xs focus:outline-none focus:border-indigo-500/50 resize-none w-full min-h-[100px]"
                    />
                  </div>
                )}
                
                {terminalTab === 'testcase' && (
                  <div className="space-y-4">
                    {problem.tests && problem.tests.length > 0 ? (
                      problem.tests.map((tc, tcIdx) => (
                        <div key={tcIdx} className="bg-[var(--bg-surface)]/60 border border-[var(--border)] p-3.5 rounded-2xl space-y-2">
                          <span className="text-slate-500 font-bold uppercase tracking-wider text-[9px] block">Test Case {tcIdx + 1} Input</span>
                          <pre className="bg-[var(--bg-base)] border border-[var(--border)] p-2.5 rounded-xl font-mono text-slate-200 overflow-x-auto text-xs">{tc.input}</pre>
                          <span className="text-slate-500 font-bold uppercase tracking-wider text-[9px] block">Expected Output</span>
                          <pre className="bg-[var(--bg-base)] border border-[var(--border)] p-2.5 rounded-xl font-mono text-indigo-300 font-bold overflow-x-auto text-xs">{tc.expected}</pre>
                        </div>
                      ))
                    ) : (
                      <div className="text-slate-600 text-center py-6">No sample test cases configured.</div>
                    )}
                  </div>
                )}

                {terminalTab === 'result' && (
                  <div className="space-y-4">
                    {!runResult && !loadingRun && (
                      <div className="text-slate-600 text-center py-10">
                        Console idle. Run or Submit code to trace results.
                      </div>
                    )}
                    
                    {(loadingRun || isSubmitting) && (
                      <div className="py-6 space-y-3">
                        <div className="flex items-center gap-3">
                          <div className="relative w-5 h-5">
                            <svg className="w-5 h-5 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth={4} />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                          </div>
                          <div>
                            <div className="text-indigo-400 font-bold text-xs">
                              {isSubmitting ? 'Submitting solution...' : 'Running code...'}
                            </div>
                            <div className="text-[10px] text-slate-500 mt-0.5">
                              Compiling &amp; executing {language.toUpperCase()} • Please wait
                            </div>
                          </div>
                        </div>
                        {/* Animated progress bar */}
                        <div className="h-1 bg-[var(--bg-surface)] rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 rounded-full animate-pulse" style={{ width: '70%', animation: 'pulse 1.5s ease-in-out infinite' }} />
                        </div>
                      </div>
                    )}

                    {runResult && !loadingRun && !isSubmitting && (
                      <div className="space-y-4 animate-fade-in">
                        
                        {/* Execution status */}
                        <div className="flex items-center justify-between border-b border-[#21262d]/40 pb-2">
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-0.5 rounded text-[9px] font-black tracking-wide uppercase ${
                              runResult.success ? 'bg-green-500/10 text-green-400 border border-green-500/20 shadow-sm shadow-green-500/5' : 'bg-red-500/10 text-red-400 border border-red-500/20 shadow-sm shadow-red-500/5'
                            }`}>
                              {runResult.success ? 'Accepted' : 'Runtime Error'}
                            </span>
                            <span className="text-slate-300 font-black uppercase tracking-wider text-[10px]">
                              {runResult.isSubmission ? 'Submission' : 'Run'} Details
                            </span>
                          </div>
                          
                          {runResult.execution_time && (
                            <span className="text-slate-500 text-[10px] font-bold">Runtime: {runResult.execution_time}</span>
                          )}
                        </div>

                        {/* Test cases outputs */}
                        {runResult.results && runResult.results.length > 0 && (
                          <div className="space-y-3">
                            {runResult.results.map((tc, tcIdx) => (
                              <div 
                                key={tcIdx}
                                className={`p-3.5 rounded-2xl border ${
                                  tc.passed 
                                    ? 'bg-green-500/5 border-green-500/10 text-green-300' 
                                    : 'bg-red-500/5 border-red-500/10 text-red-300'
                                }`}
                              >
                                <div className="font-bold mb-2 flex items-center gap-1.5 uppercase text-[9px] tracking-wider">
                                  <span className={`w-1.5 h-1.5 rounded-full ${tc.passed ? 'bg-green-500' : 'bg-red-500'}`} />
                                  Case {tcIdx + 1}: {tc.passed ? 'Passed' : 'Wrong Answer'}
                                </div>
                                
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-[10px] border-t border-[#21262d]/10">
                                  <div className="relative group">
                                    <div className="flex justify-between items-center mb-1">
                                      <div className="text-[9px] text-slate-500 font-bold uppercase">Input:</div>
                                      <button onClick={() => copyToClipboard(tc.input)} className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-white transition-opacity"><svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg></button>
                                    </div>
                                    <pre className="bg-[var(--bg-base)] border border-[var(--border)] p-2 rounded text-slate-400 overflow-x-auto leading-relaxed">{tc.input}</pre>
                                  </div>
                                  <div className="relative group">
                                    <div className="flex justify-between items-center mb-1">
                                      <div className="text-[9px] text-slate-500 font-bold uppercase">Expected:</div>
                                      <button onClick={() => copyToClipboard(tc.expected)} className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-white transition-opacity"><svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg></button>
                                    </div>
                                    <pre className={`bg-[var(--bg-base)] border p-2 rounded overflow-x-auto leading-relaxed ${
                                      tc.passed ? 'border-[var(--border)] text-slate-400' : 'border-green-500/30 text-green-400 bg-green-500/5'
                                    }`}>{tc.expected}</pre>
                                  </div>
                                  <div className="relative group">
                                    <div className="flex justify-between items-center mb-1">
                                      <div className="text-[9px] text-slate-500 font-bold uppercase">Your Output:</div>
                                      <button onClick={() => copyToClipboard(tc.output)} className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-white transition-opacity"><svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg></button>
                                    </div>
                                    <pre className={`bg-[var(--bg-base)] p-2 rounded overflow-x-auto leading-relaxed border ${
                                      tc.passed ? 'border-[var(--border)] text-slate-200' : 'border-red-500/30 text-red-400 bg-red-500/5'
                                    }`}>{tc.output}</pre>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Compilation Errors list */}
                        {runResult.errors && runResult.errors.length > 0 && (
                          <div className="space-y-2">
                            {runResult.errors.map((err, errIdx) => (
                              <div 
                                key={errIdx}
                                className="bg-[#1e1e1e] border-l-4 border-l-red-500 border-y border-r border-[#333] p-4 rounded text-red-400 relative group overflow-hidden"
                              >
                                <button onClick={() => copyToClipboard(err.message)} className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-slate-500 hover:text-white transition-opacity bg-[#2d2d2d] p-1.5 rounded-md"><svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg></button>
                                <div className="flex items-start gap-3">
                                  <svg className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <circle cx="12" cy="12" r="10" strokeWidth={2} />
                                    <line x1="12" y1="8" x2="12" y2="12" strokeWidth={2} />
                                    <line x1="12" y1="16" x2="12.01" y2="16" strokeWidth={2.5} />
                                  </svg>
                                  <div className="text-xs font-mono whitespace-pre-wrap leading-relaxed">
                                    {err.line && <span className="font-black text-white">Line {err.line}: </span>}
                                    <span className="text-red-300">{err.message}</span>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                      </div>
                    )}
                  </div>
                )}

              </div>
            )}
          </div>

        </div>

      </div>

    </div>
  );
}
