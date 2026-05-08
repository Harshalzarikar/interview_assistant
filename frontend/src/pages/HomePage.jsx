import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Clock, Globe, ArrowRight, X } from 'lucide-react';

const HomePage = () => {
  const [interviewers, setInterviewers] = useState([]);
  const [selectedInterviewer, setSelectedInterviewer] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', email: '' });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/api/interviewers`)
      .then(res => res.json())
      .then(data => {
        setInterviewers(data.interviewers);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch interviewers", err);
        setLoading(false);
      });
  }, []);

  const handleStartClick = (interviewer) => {
    setSelectedInterviewer(interviewer);
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setSubmitError('');
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/start-interview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          interviewer_id: selectedInterviewer.id,
          candidate_name: formData.name,
          candidate_email: formData.email
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `Server error: ${response.status}`);
      }

      const data = await response.json();
      if (data.token) {
        sessionStorage.setItem('interview_token', data.token);
        sessionStorage.setItem('livekit_url', data.livekit_url);
        sessionStorage.setItem('interviewer', JSON.stringify(data.interviewer));
        setShowModal(false);
        navigate(`/interview/${data.room_name}`);
      }
    } catch (err) {
      console.error('Error starting interview', err);
      setSubmitError(err.message || 'Failed to start interview. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="loading">Loading Interviewers...</div>;

  return (
    <div className="container">
      <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '32px', height: '32px', background: '#2563eb', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: '900' }}>A</div>
          <span style={{ fontSize: '1.5rem', fontWeight: '800', letterSpacing: '-0.05em' }}>artizence</span>
        </div>
        <button className="btn btn-primary" style={{ borderRadius: '999px', fontSize: '0.875rem' }}>Book a Demo</button>
      </nav>

      <section className="hero">
        <h1>Try Our Superhuman AI Interviews</h1>
        <p>Trusted by teams with taste. Experience the future of hiring with real-time, voice-enabled AI technical and behavioral assessments.</p>
        
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <span className="badge" style={{ background: '#2563eb', color: 'white' }}>All</span>
          <span className="badge">Coding</span>
          <span className="badge">Case Study</span>
          <span className="badge">Roleplay</span>
          <span className="badge">Conversational</span>
        </div>
      </section>

      <div className="interviewer-grid">
        {interviewers.map((interviewer) => (
          <div key={interviewer.id} className="interviewer-card">
            {interviewer.is_new && <span className="badge badge-new">New</span>}
            <div className={`badge`} style={{ position: 'absolute', top: '1rem', left: '1rem', background: '#000', color: '#fff' }}>
              {interviewer.type}
            </div>
            
            <img 
              src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${interviewer.name}`} 
              alt={interviewer.name} 
              className="interviewer-avatar"
            />
            
            <h3 className="card-title">{interviewer.name}</h3>
            <p className="card-role">{interviewer.role}</p>
            
            <div className="card-tags">
              {interviewer.tags.map(tag => <span key={tag} className="tag">{tag}</span>)}
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <img src={`https://logo.clearbit.com/${interviewer.company.toLowerCase()}.com`} alt={interviewer.company} style={{ height: '24px', opacity: 0.6 }} />
            </div>

            <div className="card-footer">
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Clock size={14} /> {interviewer.duration}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Globe size={14} /> {interviewer.language}
              </span>
            </div>

            <button 
              className="btn btn-primary btn-block" 
              style={{ marginTop: '1.5rem' }}
              onClick={() => handleStartClick(interviewer)}
            >
              Try Interview <ArrowRight size={18} />
            </button>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <button className="close-btn" style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => setShowModal(false)}>
              <X size={24} />
            </button>
            <h2 style={{ textAlign: 'center', marginBottom: '0.5rem' }}>You are just a step away</h2>
            <p style={{ textAlign: 'center', color: '#666', marginBottom: '2rem' }}>Enter your details to begin a tailored AI-powered interview with {selectedInterviewer.name}.</p>
            
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
              <div style={{ width: '80px', height: '80px', background: '#1e293b', borderRadius: '1rem', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '2rem', fontWeight: 'bold' }}>
                {selectedInterviewer.type === 'Coding' ? 'AI' : selectedInterviewer.name[0]}
              </div>
              <p style={{ fontWeight: '700', marginTop: '1rem', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.1em' }}>{selectedInterviewer.role}</p>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Full Name</label>
                <input 
                  type="text" 
                  placeholder="John Smith" 
                  required 
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Business Email</label>
                <input 
                  type="email" 
                  placeholder="john.smith@company.com" 
                  required 
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
              <button type="submit" className="btn btn-primary btn-block" style={{ padding: '1rem' }} disabled={submitting}>
                {submitting ? 'Starting...' : 'Start AI Interview'}
              </button>
              {submitError && (
                <p style={{ textAlign: 'center', fontSize: '0.875rem', marginTop: '0.75rem', color: '#ef4444', background: '#fee2e2', padding: '0.75rem', borderRadius: '8px' }}>
                  ⚠ {submitError}
                </p>
              )}
              <p style={{ textAlign: 'center', fontSize: '0.75rem', marginTop: '1rem', color: '#666' }}>
                ⓘ We will not spam you, pinky promise!
              </p>
            </form>
          </div>
        </div>
      )}

      <footer style={{ marginTop: '5rem', padding: '2rem 0', textAlign: 'center', color: '#666', borderTop: '1px solid var(--border)' }}>
        <p>© 2024 Artizence Labs Inc. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default HomePage;
