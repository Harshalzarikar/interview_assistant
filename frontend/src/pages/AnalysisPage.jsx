import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, AlertTriangle, ArrowLeft } from 'lucide-react';

const AnalysisPage = () => {
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

  return (
    <div className="container" style={{ maxWidth: '800px', margin: '0 auto', paddingTop: '3rem' }}>
      <button className="btn" style={{ background: 'transparent', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '2rem', padding: 0 }} onClick={() => navigate('/')}>
        <ArrowLeft size={18} /> Back to Home
      </button>

      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '3rem', margin: '0 0 1rem 0' }}>Interview Report</h1>
        <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: '#2563eb', color: 'white', width: '120px', height: '120px', borderRadius: '50%', fontSize: '3rem', fontWeight: 'bold', border: '8px solid #3b82f6' }}>
          {analysis.score}<span style={{ fontSize: '1.5rem', opacity: 0.8 }}>/10</span>
        </div>
      </div>

      <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '1.5rem', marginBottom: '2rem' }}>
        <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#22c55e' }}>
          <CheckCircle /> Key Strengths
        </h3>
        <ul style={{ paddingLeft: '1.5rem', color: '#e2e8f0', lineHeight: '1.6' }}>
          {analysis.strengths?.map((item, idx) => (
            <li key={idx} style={{ marginBottom: '0.5rem' }}>{item}</li>
          ))}
        </ul>
      </div>

      <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '1.5rem', marginBottom: '2rem' }}>
        <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#ef4444' }}>
          <AlertTriangle /> Areas for Improvement
        </h3>
        <ul style={{ paddingLeft: '1.5rem', color: '#e2e8f0', lineHeight: '1.6' }}>
          {analysis.weaknesses?.map((item, idx) => (
            <li key={idx} style={{ marginBottom: '0.5rem' }}>{item}</li>
          ))}
        </ul>
      </div>

      <div style={{ background: '#1e293b', padding: '2rem', borderRadius: '1.5rem', marginBottom: '4rem' }}>
        <h3 style={{ marginTop: 0, color: '#f8fafc' }}>Overall Feedback</h3>
        <p style={{ color: '#cbd5e1', lineHeight: '1.6', margin: 0 }}>
          {analysis.feedback}
        </p>
      </div>
    </div>
  );
};

export default AnalysisPage;
