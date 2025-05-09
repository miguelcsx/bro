import React, { useState } from 'react';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setMessages(prev => [...prev, {role: 'user', content: query}]);
    setQuery('');
    setLoading(true);

    // Simulate API call
    setTimeout(() => {
      setMessages(prev => [...prev, {role: 'assistant', content: 'This would be the API response'}]);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="app">
      <div className="header">
        <div className="logo-container">
          <div className="logo-icon">💸</div>
          <div className="logo-text">
            <h1>Hey, I'm Bro</h1>
            <p>What stocks would you like to see today?</p>
          </div>
        </div>
      </div>

      <div className="chat-container">
        {messages.length > 0 ? (
          <div className="messages">
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                {msg.content}
              </div>
            ))}
            {loading && <div className="message assistant">Bro is thinking...</div>}
          </div>
        ) : (
          <div className="empty-state">
            <div className="search-box">
              <input
                type="text"
                placeholder="Ask about stocks, investments or anything financial"
                readOnly
              />
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="input-container">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Message Bro"
          />
          <button type="submit">→</button>
        </form>
      </div>
    </div>
  );
}

export default App;
