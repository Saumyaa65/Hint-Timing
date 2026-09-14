import React from 'react'

export default function HintsPanel({hints, onRequestHint, loading}){
  // Format timestamp if available
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return '';
    }
  };
  
  return (
    <div className="hints-panel">
      <div style={{
        display:'flex', 
        justifyContent:'space-between', 
        alignItems:'center',
        borderBottom: '1px solid #f3f4f6',
        paddingBottom: '8px',
        marginBottom: '12px'
      }}>
        <h4 style={{margin: 0, fontSize: '16px'}}>Hints</h4>
        <button 
          onClick={onRequestHint} 
          disabled={loading}
          style={{
            backgroundColor: loading ? '#e5e7eb' : '#6366f1', 
            opacity: loading ? 0.7 : 1
          }}
        >
          {loading? 'Generating...' : 'Request Hint'}
        </button>
      </div>
      <div>
        {hints && hints.length > 0 ? (
          <div>
            {hints.map((h,i) => (
              <div key={i} className="hint-item" style={{
                position: 'relative',
                borderLeft: `4px solid ${getLevelColor(h.level)}`,
                paddingLeft: '12px',
                background: '#fff8e1',
                marginBottom: '12px'
              }}>
                <div className="hint-meta" style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '4px'
                }}>
                  <span style={{fontWeight: '500'}}>Level {h.level || 'N/A'}</span>
                  {h.timestamp && <span style={{color: '#9ca3af', fontSize: '12px'}}>{formatTime(h.timestamp)}</span>}
                </div>
                <div className="hint-content" style={{fontSize: '15px'}}>{h.content}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-hints" style={{
            padding: '20px',
            textAlign: 'center',
            color: '#6b7280',
            backgroundColor: '#f9fafb',
            borderRadius: '6px'
          }}>
            <p style={{margin: 0}}>No hints yet.</p>
            <p style={{margin: '8px 0 0 0', fontSize: '14px'}}>Request a hint if you're stuck!</p>
          </div>
        )}
      </div>
    </div>
  )
}

// Helper function to get color for different hint levels
function getLevelColor(level) {
  switch (level) {
    case 1: return '#10b981'; // Green - gentle
    case 2: return '#3b82f6'; // Blue - more specific
    case 3: return '#f59e0b'; // Yellow - quite detailed
    case 4: return '#ef4444'; // Red - very detailed
    default: return '#6366f1'; // Default purple
  }
}
