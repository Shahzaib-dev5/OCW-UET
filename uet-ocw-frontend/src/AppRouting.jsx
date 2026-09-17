import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import AboutPage from './pages/AboutPage'
import CoursePage from './pages/CoursePage'
import CourseDetailPage from './pages/CourseDetailPage'
import InternshipPage from './pages/InternshipPage'
import InternshipDetailPage from './pages/InternshipDetailPage'
import ResearchPage from './pages/ResearchPage'
import ResearchDetailPage from './pages/ResearchDetailPage'

export default function AppRouting() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/courses" element={<CoursePage />} />
          <Route path="/courses/:courseId" element={<CourseDetailPage />} />
          <Route path="/internships" element={<InternshipPage />} />
          <Route path="/internships/:internshipId" element={<InternshipDetailPage />} />
          <Route path="/research" element={<ResearchPage />} />
          <Route path="/research/:researchId" element={<ResearchDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
