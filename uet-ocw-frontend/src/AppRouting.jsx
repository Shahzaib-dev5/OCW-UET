import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import AboutPage from './pages/AboutPage'
import CoursePage from './pages/CoursePage'
import CourseDetailPage from './pages/CourseDetailPage'
import CourseEditorPage from './pages/CourseEditorPage'
import BooksPage from './pages/BooksPage'
import InternshipPage from './pages/InternshipPage'
import InternshipDetailPage from './pages/InternshipDetailPage'
import InvitedTalkPage from './pages/InvitedTalkPage'
import InvitedTalkDetailPage from './pages/InvitedTalkDetailPage'
import ResearchPage from './pages/ResearchPage'
import ResearchDetailPage from './pages/ResearchDetailPage'
import AccountPage from './pages/AccountPage'
import AuthPage from './pages/AuthPage'
import MyCoursesPage from './pages/MyCoursesPage'
import AdminPage from './pages/AdminPage'

export default function AppRouting() {
  return (
    <BrowserRouter>
      <AuthProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/courses" element={<CoursePage />} />
          <Route path="/courses/new" element={<CourseEditorPage />} />
          <Route path="/courses/:courseId" element={<CourseDetailPage />} />
          <Route path="/books" element={<BooksPage />} />
          <Route path="/skills-development" element={<InternshipPage />} />
          <Route path="/skills-development/:internshipId" element={<InternshipDetailPage />} />
          <Route path="/invited-talks" element={<InvitedTalkPage />} />
          <Route path="/invited-talks/:talkId" element={<InvitedTalkDetailPage />} />
          <Route path="/internships" element={<Navigate to="/skills-development" replace />} />
          <Route path="/internships/:internshipId" element={<LegacySkillsDevelopmentRedirect />} />
          <Route path="/research" element={<ResearchPage />} />
          <Route path="/research/:researchId" element={<ResearchDetailPage />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/signup" element={<AuthPage mode="signup" />} />
          <Route path="/account" element={<AccountPage />} />
          <Route path="/my-courses" element={<MyCoursesPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
      </AuthProvider>
    </BrowserRouter>
  )
}

function LegacySkillsDevelopmentRedirect() {
  const { internshipId } = useParams()
  return <Navigate to={`/skills-development/${internshipId}`} replace />
}
