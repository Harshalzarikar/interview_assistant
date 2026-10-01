import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, AlertTriangle, ArrowLeft, Target, ListChecks, Gauge } from 'lucide-react';

const card = {
  background: '#1e293b',
  padding: '2rem',
  borderRadius: '1.5rem',
  marginBottom: '2rem',
};

const sectionTitle = {
  marginTop: 0,
  display: 'flex',
  alignItems: 'center',
  gap: '0.5rem',
};

const list = { paddingLeft: '1.5rem', color: '#e2e8f0', lineHeight: '1.6', margin: 0 };

const ratingColor = (rating) => {
  if (rating === 'strong') return '#22c55e';
  if (rating === 'weak') return '#ef4444';
  return '#f59e0b';
};

function ScoreBar({ label, score, comment }) {
  const value = typeof score === 'number' ? score : 0;
  const clamped = Math.max(0, Math.min(10, value));
  return (
    <div style={{ marginBottom: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.375rem' }}>
        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{label}</span>
        <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>{value}/10</span>
      </div>
      <div style={{ height: '8px', background: '#334155', borderRadius: '999px', overflow: 'hidden' }}>
        <div style={{ width: `${clamped * 10}%`, height: '100%', background: '#2563eb', borderRadius: '999px' }} />
      </div>
      {comment && <p style={{ margin: '0.4rem 0 0', color: '#94a3b8', fontSize: '0.8rem' }}>{comment}</p>}
    </div>
  );
}

export default function AnalysisPage() {
  const navigate = useNavigate();
  const analysisRaw = sessionStorage.getItem('interview_analysis');

  if (!analysisRaw) {
    return (
      <div className="container" style={{ textAlign: 'center', marginTop: '5rem' }}>
        <h2>No analysis found</h2>
        <button className="btn btn-primary" onClick={() => navigate('/')}>Go Home</button>
      </div>
    );
  }

  const analysis = JSON.parse(analysisRaw);
  const dimensions = analysis.dimensions || [];
  const strengths = analysis.strengths || [];
  const weaknesses = analysis.weaknesses || [];
  const recommendations = analysis.recommendations || [];
  const breakdown = analysis.question_breakdown || [];

  return (
    <div className="container" style={{ maxWidth: '820px', margin: '0 auto', paddingTop: '3rem' }}>
      <button className="btn" style={{ background: 'transparent', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '2rem', padding: 0 }} onClick={() => navigate('/')}>
        <ArrowLeft size={18} /> Back to Home
      </button>

      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '3rem', margin: '0 0 1.5rem 0' }}>Interview Report</h1>
        <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: '#2563eb', color: 'white', width: '120px', height: '120px', borderRadius: '50%', fontSize: '3rem', fontWeight: 'bold', border: '8px solid #3b82f6' }}>
          {analysis.score}<span style={{ fontSize: '1.5rem', opacity: 0.8 }}>/10</span>
        </div>
        {analysis.readiness && (
          <div style={{ marginTop: '1.25rem' }}>
            <span style={{ display: 'inline-block', background: '#334155', color: '#e2e8f0', padding: '0.4rem 1rem', borderRadius: '999px', fontSize: '0.875rem', fontWeight: 600 }}>
              {analysis.readiness}
            </span>
          </div>
        )}
      </div>

      {analysis.summary && (
        <div style={card}>
          <h3 style={{ ...sectionTitle, color: '#f8fafc' }}><Gauge size={20} /> Summary</h3>
          <p style={{ color: '#cbd5e1', lineHeight: '1.6', margin: 0 }}>{analysis.summary}</p>
        </div>
      )}

      {dimensions.length > 0 && (
        <div style={card}>
          <h3 style={{ ...sectionTitle, color: '#93c5fd', marginBottom: '1.5rem' }}><Target size={20} /> Score Breakdown</h3>
          {dimensions.map((dim, idx) => (
            <ScoreBar key={idx} label={dim.name} score={dim.score} comment={dim.comment} />
          ))}
        </div>
      )}

      <div style={card}>
        <h3 style={{ ...sectionTitle, color: '#22c55e' }}><CheckCircle /> Key Strengths</h3>
        <ul style={list}>
          {strengths.map((item, idx) => (
            <li key={idx} style={{ marginBottom: '0.5rem' }}>{item}</li>
          ))}
        </ul>
      </div>

      <div style={card}>
        <h3 style={{ ...sectionTitle, color: '#ef4444' }}><AlertTriangle /> Areas for Improvement</h3>
        <ul style={list}>
          {weaknesses.map((item, idx) => (
            <li key={idx} style={{ marginBottom: '0.5rem' }}>{item}</li>
          ))}
        </ul>
      </div>

      {breakdown.length > 0 && (
        <div style={card}>
          <h3 style={{ ...sectionTitle, color: '#f8fafc', marginBottom: '1.5rem' }}><ListChecks size={20} /> Question-by-Question</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {breakdown.map((item, idx) => (
              <div key={idx} style={{ borderLeft: `3px solid ${ratingColor(item.rating)}`, paddingLeft: '1rem' }}>
                <p style={{ margin: 0, fontWeight: 600, color: '#e2e8f0' }}>{item.question}</p>
                <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: ratingColor(item.rating), fontWeight: 700 }}>
                  {item.rating}
                </span>
                {item.comment && <p style={{ margin: '0.35rem 0 0', color: '#94a3b8', fontSize: '0.875rem', lineHeight: 1.5 }}>{item.comment}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {analysis.feedback && (
        <div style={card}>
          <h3 style={{ ...sectionTitle, color: '#f8fafc' }}>Overall Feedback</h3>
          <p style={{ color: '#cbd5e1', lineHeight: '1.6', margin: 0 }}>{analysis.feedback}</p>
        </div>
      )}

      {recommendations.length > 0 && (
        <div style={{ ...card, marginBottom: '4rem' }}>
          <h3 style={{ ...sectionTitle, color: '#93c5fd' }}><ListChecks size={20} /> Next Steps</h3>
          <ol style={list}>
            {recommendations.map((item, idx) => (
              <li key={idx} style={{ marginBottom: '0.5rem' }}>{item}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
