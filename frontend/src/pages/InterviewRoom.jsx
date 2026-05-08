import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  LiveKitRoom, 
  RoomAudioRenderer,
  useLocalParticipant,
  useConnectionState,
  useRemoteParticipants,
  useTrackTranscription,
  useTracks,
} from '@livekit/components-react';
import { ConnectionState, Track, RoomEvent } from 'livekit-client';
import { Mic, MicOff, PhoneOff, Settings, Shield, MessageSquare } from 'lucide-react';
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

/* ───────────────────── Transcript Panel ───────────────────── */
const TranscriptPanel = () => {
  const [messages, setMessages] = useState([]);
  const scrollRef = useRef(null);
  const remoteParticipants = useRemoteParticipants();

  // Get all audio tracks (agent + local) for transcription
  const tracks = useTracks(
    [{ source: Track.Source.Microphone, withPlaceholder: false }],
    { onlySubscribed: true }
  );

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Listen for transcription events from the room
  const { localParticipant } = useLocalParticipant();

  useEffect(() => {
    if (!localParticipant) return;
    const room = localParticipant.room;
    if (!room) return;

    const handleTranscription = (segments, participant) => {
      if (!segments || segments.length === 0) return;
      
      const isAgent = participant?.identity !== localParticipant.identity;
      
      segments.forEach((segment) => {
        const text = segment.text?.trim();
        if (!text) return;
        
        setMessages(prev => {
          // Check if this is an update to an existing segment
          const existingIdx = prev.findIndex(m => m.id === segment.id);
          if (existingIdx !== -1) {
            const updated = [...prev];
            updated[existingIdx] = {
              ...updated[existingIdx],
              text,
              isFinal: segment.final,
            };
            return updated;
          }
          // New segment
          return [...prev, {
            id: segment.id,
            text,
            isAgent,
            isFinal: segment.final,
            timestamp: new Date(),
            speakerName: isAgent 
              ? (participant?.name || 'AI Interviewer') 
              : 'You',
          }];
        });
      });
    };

    room.on(RoomEvent.TranscriptionReceived, handleTranscription);
    return () => {
      room.off(RoomEvent.TranscriptionReceived, handleTranscription);
    };
  }, [localParticipant]);

  return (
    <div style={{
      background: '#1e293b',
      padding: '1.5rem',
      borderRadius: '1.5rem',
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      minHeight: '200px',
      maxHeight: '400px',
    }}>
      <h4 style={{ 
        margin: '0 0 1rem 0', 
        color: '#94a3b8', 
        textTransform: 'uppercase', 
        fontSize: '0.75rem', 
        letterSpacing: '0.05em',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
      }}>
        <MessageSquare size={14} /> Live Transcript
      </h4>
      <div 
        ref={scrollRef}
        style={{ 
          flex: 1, 
          overflowY: 'auto', 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '0.75rem',
          scrollBehavior: 'smooth',
        }}
      >
        {messages.length === 0 ? (
          <p style={{ color: '#475569', fontSize: '0.875rem', textAlign: 'center', marginTop: '2rem' }}>
            Conversation will appear here...
          </p>
        ) : (
          messages.filter(m => m.text.length > 0).map((msg) => (
            <div key={msg.id} style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: msg.isAgent ? 'flex-start' : 'flex-end',
            }}>
              <span style={{ 
                fontSize: '0.625rem', 
                color: '#64748b', 
                marginBottom: '0.25rem',
                fontWeight: '600',
              }}>
                {msg.speakerName}
              </span>
              <div style={{
                background: msg.isAgent ? '#334155' : '#2563eb',
                color: '#fff',
                padding: '0.5rem 0.75rem',
                borderRadius: msg.isAgent ? '0 12px 12px 12px' : '12px 0 12px 12px',
                fontSize: '0.875rem',
                maxWidth: '90%',
                lineHeight: '1.4',
                opacity: msg.isFinal ? 1 : 0.7,
                fontStyle: msg.isFinal ? 'normal' : 'italic',
              }}>
                {msg.text}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

/* ───────────────────── Main Interview UI ───────────────────── */
const InterviewUI = ({ interviewer }) => {
  const navigate = useNavigate();
  const { localParticipant } = useLocalParticipant();
  const connectionState = useConnectionState();
  const [isMuted, setIsMuted] = useState(false);

  // Ensure microphone is enabled once connected
  useEffect(() => {
    if (connectionState === ConnectionState.Connected && localParticipant) {
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

        <div style={{ width: '340px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Microphone Status */}
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

          {/* Live Transcript */}
          <TranscriptPanel />

          {/* Interview Info */}
          <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '1.5rem' }}>
            <h4 style={{ margin: '0 0 1rem 0', color: '#94a3b8', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Interview Info</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div>
                <span className="badge" style={{ background: '#334155', color: '#fff', marginBottom: '0.25rem' }}>Type</span>
                <p style={{ margin: 0 }}>{interviewer.type}</p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#22c55e', fontSize: '0.875rem' }}>
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
