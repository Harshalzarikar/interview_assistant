import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function JoinInterviewPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function loadSession() {
      try {
        const response = await fetch(`${API_BASE}/api/mock-interviews/${sessionId}/join`);
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.detail || `Unable to join (${response.status})`);
        }
        const data = await response.json();
        if (cancelled) return;

        sessionStorage.setItem('interview_token', data.token);
        sessionStorage.setItem('livekit_url', data.livekit_url);
        sessionStorage.setItem('interviewer', JSON.stringify(data.interviewer));
        sessionStorage.setItem('candidate_name', data.candidate_name || 'Candidate');
        sessionStorage.setItem('mock_session_id', data.session_id);
        navigate(`/interview/${data.room_name}`, { replace: true });
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to open interview link.');
        }
      }
    }

    loadSession();
    return () => {
      cancelled = true;
    };
  }, [sessionId, navigate]);

  if (error) {
    return (
      <div className="container" style={{ paddingTop: '4rem', textAlign: 'center' }}>
        <h2>Interview link unavailable</h2>
        <p style={{ color: '#94a3b8' }}>{error}</p>
      </div>
    );
  }

  return (
    <div className="loading" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      Preparing your interview...
    </div>
  );
}
