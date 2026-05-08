import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  LiveKitRoom, 
  RoomAudioRenderer,
  useLocalParticipant,
  useConnectionState,
} from '@livekit/components-react';
import { ConnectionState } from 'livekit-client';
import { Mic, MicOff, PhoneOff, Settings, Shield } from 'lucide-react';
import '@livekit/components-styles';

const InterviewRoom = () => {
  const { roomName } = useParams();
  const navigate = useNavigate();
  const token = sessionStorage.getItem('interview_token');
  const interviewer = JSON.parse(sessionStorage.getItem('interviewer') || '{}');
  
  if (!token) {
    navigate('/');
    return null;
  }

  return (
    <div className="interview-room">
      <LiveKitRoom
        video={false}
        audio={true}
        token={token}
        serverUrl={import.meta.env.VITE_LIVEKIT_URL || 'wss://agent-creation-qcaw3q8p.livekit.cloud'}
        onDisconnected={() => navigate('/')}
        connect={true}
      >
        <InterviewUI interviewer={interviewer} />
        <RoomAudioRenderer />
      </LiveKitRoom>
    </div>
  );
};

const InterviewUI = ({ interviewer }) => {
  const navigate = useNavigate();
  const { localParticipant } = useLocalParticipant();
  const connectionState = useConnectionState();
  const [isMuted, setIsMuted] = useState(false);

  // Ensure microphone is enabled once connected
  useEffect(() => {
    if (connectionState === ConnectionState.Connected && localParticipant) {
      // Force-enable the microphone on connect to guarantee audio is publishing
      localParticipant.setMicrophoneEnabled(true).then(() => {
        setIsMuted(false);
        console.log('[InterviewRoom] Microphone enabled, audio is publishing.');
      }).catch((err) => {
        console.error('[InterviewRoom] Failed to enable microphone:', err);
      });
    }
  }, [connectionState, localParticipant]);

  // Sync mute state with the actual track state
  useEffect(() => {
    if (localParticipant) {
      setIsMuted(!localParticipant.isMicrophoneEnabled);
    }
  }, [localParticipant?.isMicrophoneEnabled]);

  const toggleMic = useCallback(async () => {
    if (!localParticipant) return;
    // If currently muted → enable mic; if currently on → mute it
    const shouldEnable = isMuted;
    await localParticipant.setMicrophoneEnabled(shouldEnable);
    setIsMuted(!shouldEnable);
  }, [localParticipant, isMuted]);

  const getStatusText = () => {
    switch (connectionState) {
      case ConnectionState.Connecting: return 'Connecting...';
      case ConnectionState.Connected: return 'Live';
      case ConnectionState.Reconnecting: return 'Reconnecting...';
      case ConnectionState.Disconnected: return 'Disconnected';
      default: return 'Connecting...';
    }
  };

  const getStatusColor = () => {
    return connectionState === ConnectionState.Connected ? '#22c55e' : '#f59e0b';
  };

  return (
    <>
      <header className="interview-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: '40px', height: '40px', background: '#2563eb', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: '900' }}>A</div>
          <div>
            <h3 style={{ margin: 0, fontSize: '1rem' }}>Interview with {interviewer.name}</h3>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ width: '8px', height: '8px', background: getStatusColor(), borderRadius: '50%' }}></span> {getStatusText()}
            </span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="control-btn" style={{ width: '40px', height: '40px' }}><Settings size={20} /></button>
          <button className="control-btn" style={{ width: '40px', height: '40px', color: '#ef4444' }} onClick={() => navigate('/')}><PhoneOff size={20} /></button>
        </div>
      </header>

      <main className="interview-main">
        <div className="video-container">
          <div className="video-slot">
            <div style={{ textAlign: 'center' }}>
              <img 
                src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${interviewer.name}`} 
                alt={interviewer.name} 
                className="agent-avatar-large"
                style={{ border: '4px solid #2563eb' }}
              />
              <h2 style={{ marginTop: '1.5rem', fontSize: '2.5rem' }}>{interviewer.name}</h2>
              <p style={{ color: '#94a3b8', fontSize: '1.125rem' }}>{interviewer.role}</p>
            </div>
            
            <div className="visualizer-overlay">
              <div className="visualizer-bar" style={{ animationDelay: '0s' }}></div>
              <div className="visualizer-bar" style={{ animationDelay: '0.1s' }}></div>
              <div className="visualizer-bar" style={{ animationDelay: '0.2s' }}></div>
              <div className="visualizer-bar" style={{ animationDelay: '0.3s' }}></div>
              <div className="visualizer-bar" style={{ animationDelay: '0.4s' }}></div>
              <div className="visualizer-bar" style={{ animationDelay: '0.5s' }}></div>
            </div>
          </div>
        </div>

        <div style={{ width: '300px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '1.5rem' }}>
            <h4 style={{ margin: '0 0 1rem 0', color: '#94a3b8', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Your Audio</h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ width: '48px', height: '48px', background: isMuted ? '#ef4444' : '#2563eb', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', transition: 'background 0.2s' }} onClick={toggleMic}>
                {isMuted ? <MicOff size={24} /> : <Mic size={24} />}
              </div>
              <div>
                <p style={{ margin: 0, fontWeight: '600' }}>{isMuted ? 'Microphone Muted' : 'Microphone On'}</p>
                <p style={{ margin: 0, fontSize: '0.75rem', color: '#94a3b8' }}>
                  {connectionState === ConnectionState.Connected 
                    ? (isMuted ? 'Click to unmute' : 'Agent can hear you') 
                    : 'Waiting for connection...'}
                </p>
              </div>
            </div>
          </div>

          <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '1.5rem', flex: 1 }}>
            <h4 style={{ margin: '0 0 1rem 0', color: '#94a3b8', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Interview Info</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <span className="badge" style={{ background: '#334155', color: '#fff', marginBottom: '0.5rem' }}>Type</span>
                <p style={{ margin: 0 }}>{interviewer.type}</p>
              </div>
              <div>
                <span className="badge" style={{ background: '#334155', color: '#fff', marginBottom: '0.5rem' }}>Focus Areas</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {interviewer.tags?.map(tag => <span key={tag} style={{ fontSize: '0.875rem', color: '#94a3b8' }}>• {tag}</span>)}
                </div>
              </div>
              <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#22c55e', fontSize: '0.875rem' }}>
                <Shield size={16} /> Encryption Enabled
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="controls">
        <button 
          className={`control-btn ${isMuted ? 'active' : ''}`} 
          onClick={toggleMic}
        >
          {isMuted ? <MicOff size={24} /> : <Mic size={24} />}
        </button>
        <button className="control-btn" style={{ background: '#ef4444', width: '120px', borderRadius: '999px', fontSize: '1rem', fontWeight: 'bold' }} onClick={() => navigate('/')}>
          End Interview
        </button>
      </footer>
    </>
  );
};

export default InterviewRoom;
