import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import InterviewRoom from './pages/InterviewRoom'
import AnalysisPage from './pages/AnalysisPage'
import JoinInterviewPage from './pages/JoinInterviewPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/join/:sessionId" element={<JoinInterviewPage />} />
      <Route path="/interview/:roomName" element={<InterviewRoom />} />
      <Route path="/analysis" element={<AnalysisPage />} />
    </Routes>
  )
}
