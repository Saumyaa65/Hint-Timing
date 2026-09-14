import React from 'react'

export default function TopicFilter({topics, selected, onSelect, difficulty, onDifficultyChange}) {
  const difficulties = ['All', 'Easy', 'Medium', 'Hard'];
  
  return (
    <div className="filter-container">
      <div className="filter-header">
        <h3 className="filter-title">Filter Problems</h3>
        <div className="filter-subtitle">Find problems by topic or difficulty level</div>
      </div>
      
      <div className="filter-controls">
        <div className="filter-group">
          <label className="filter-label" htmlFor="topic-select">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
              <polyline points="2 17 12 22 22 17"></polyline>
              <polyline points="2 12 12 17 22 12"></polyline>
            </svg>
            Topic
          </label>
          <div className="select-wrapper">
            <select 
              id="topic-select"
              value={selected || ''}
              onChange={e => onSelect(e.target.value)}
              className="topic-select"
            >
              <option value="">All Topics</option>
              {Array.isArray(topics) && topics.map(topic => (
                <option key={topic.name} value={topic.name}>
                  {topic.name} ({topic.count})
                </option>
              ))}
            </select>
            <svg className="select-arrow" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>
        </div>
        
        <div className="filter-group">
          <label className="filter-label">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
            </svg>
            Difficulty
          </label>
          <div className="difficulty-buttons">
            {difficulties.map(diff => (
              <button 
                key={diff}
                onClick={() => onDifficultyChange?.(diff === 'All' ? '' : diff)}
                className={`difficulty-btn difficulty-${diff.toLowerCase()} ${
                  (difficulty === diff || (diff === 'All' && !difficulty)) ? 'active' : ''
                }`}
              >
                {diff === 'All' ? 'All' : 
                  <span className="difficulty-content">
                    {diff === 'Easy' && (
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 22C6.5 22 2 17.5 2 12S6.5 2 12 2s10 4.5 10 10-4.5 10-10 10z"></path>
                        <path d="M8 14s1.5 2 4 2 4-2 4-2"></path>
                        <line x1="9" y1="9" x2="9.01" y2="9"></line>
                        <line x1="15" y1="9" x2="15.01" y2="9"></line>
                      </svg>
                    )}
                    {diff === 'Medium' && (
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 22C6.5 22 2 17.5 2 12S6.5 2 12 2s10 4.5 10 10-4.5 10-10 10z"></path>
                        <line x1="8" y1="12" x2="16" y2="12"></line>
                        <line x1="9" y1="9" x2="9.01" y2="9"></line>
                        <line x1="15" y1="9" x2="15.01" y2="9"></line>
                      </svg>
                    )}
                    {diff === 'Hard' && (
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 22C6.5 22 2 17.5 2 12S6.5 2 12 2s10 4.5 10 10-4.5 10-10 10z"></path>
                        <path d="M16 16s-1.5-2-4-2-4 2-4 2"></path>
                        <line x1="9" y1="9" x2="9.01" y2="9"></line>
                        <line x1="15" y1="9" x2="15.01" y2="9"></line>
                      </svg>
                    )}
                    <span>{diff}</span>
                  </span>
                }
              </button>
            ))}
          </div>
        </div>
      </div>

      <style jsx>{`
        .filter-container {
          background: white;
          border-radius: var(--radius-lg);
          box-shadow: var(--shadow-md);
          padding: 1.5rem;
          margin-bottom: 2rem;
          position: relative;
          overflow: hidden;
        }
        
        .filter-container::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 4px;
          background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        }
        
        .filter-header {
          margin-bottom: 1.25rem;
        }
        
        .filter-title {
          margin: 0;
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--gray-900);
        }
        
        .filter-subtitle {
          font-size: 0.875rem;
          color: var(--gray-500);
          margin-top: 0.25rem;
        }
        
        .filter-controls {
          display: flex;
          flex-wrap: wrap;
          gap: 1.5rem;
        }
        
        .filter-group {
          flex: 1;
          min-width: 200px;
        }
        
        .filter-label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-weight: 500;
          color: var(--gray-700);
          margin-bottom: 0.5rem;
          font-size: 0.875rem;
        }
        
        .select-wrapper {
          position: relative;
        }
        
        .select-arrow {
          position: absolute;
          right: 12px;
          top: 50%;
          transform: translateY(-50%);
          color: var(--gray-400);
          pointer-events: none;
        }
        
        .topic-select {
          width: 100%;
          padding: 0.75rem 1rem;
          border-radius: var(--radius-md);
          border: 1px solid var(--gray-300);
          background-color: white;
          font-size: 0.95rem;
          color: var(--gray-800);
          -webkit-appearance: none;
          appearance: none;
          padding-right: 2.5rem;
          transition: all 0.2s ease;
        }
        
        .topic-select:focus {
          outline: none;
          border-color: var(--primary-color);
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        .difficulty-buttons {
          display: flex;
          border-radius: var(--radius-md);
          overflow: hidden;
          border: 1px solid var(--gray-300);
        }
        
        .difficulty-btn {
          flex: 1;
          padding: 0.75rem 0;
          background-color: white;
          border: none;
          font-size: 0.95rem;
          font-weight: 500;
          color: var(--gray-700);
          cursor: pointer;
          transition: all 0.2s ease;
          position: relative;
        }
        
        .difficulty-btn:not(:last-child) {
          border-right: 1px solid var(--gray-300);
        }
        
        .difficulty-content {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.4rem;
        }
        
        .difficulty-btn.active {
          color: white;
        }
        
        .difficulty-btn.active::after {
          content: '';
          position: absolute;
          bottom: 5px;
          left: 50%;
          transform: translateX(-50%);
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background-color: rgba(255, 255, 255, 0.7);
        }
        
        /* Difficulty button colors */
        .difficulty-all.active {
          background-color: var(--primary-color);
        }
        
        .difficulty-easy.active {
          background-color: var(--secondary-color);
        }
        
        .difficulty-medium.active {
          background-color: var(--warning-color);
        }
        
        .difficulty-hard.active {
          background-color: var(--danger-color);
        }
        
        @media (max-width: 640px) {
          .filter-controls {
            flex-direction: column;
            gap: 1rem;
          }
        }
      `}</style>
    </div>
  )
}
