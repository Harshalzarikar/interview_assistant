import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import InterviewRoom from './pages/InterviewRoom'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/interview/:roomName" element={<InterviewRoom />} />
    </Routes>
  )
}
