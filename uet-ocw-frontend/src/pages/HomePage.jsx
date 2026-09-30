import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchJson, fileUrl } from '../data/api'

export default function HomePage() {
  const [courses, setCourses] = useState([])
  const [internships, setInternships] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadHomeData() {
      try {
        setLoading(true)
        setError('')
        const [coursesData, internshipsData] = await Promise.all([
          fetchJson('/courses'),
          fetchJson('/internships'),
        ])

        setCourses(coursesData)
        setInternships(internshipsData)
      } catch (loadError) {
        setError(loadError.message || 'Unable to load homepage information.')
      } finally {
        setLoading(false)
      }
    }

    loadHomeData()
  }, [])

  const featuredCourses = useMemo(() => courses.slice(0, 3), [courses])
  const featuredInternships = useMemo(() => internships.slice(0, 3), [internships])

  return (
    <div className="home-page">
      <section className="home-hero-banner">
        <div className="container">
          <div className="home-hero-content">
            <p className="eyebrow">UET Open Courseware</p>
            <h2>Learning resources, courses and opportunities in one place.</h2>
            <p>
              Explore academic modules, course material, research work and internship pathways from the University of Engineering and Technology.
            </p>
            <div className="home-hero-actions">
              <Link className="primary-button" to="/courses">Explore Courses</Link>
              <Link className="secondary-button light" to="/internships">View Internships</Link>
            </div>
          </div>
        </div>
      </section>

      <div className="container page-block">
        {error && <div className="alert-box">{error}</div>}

        <section className="home-section-heading">
          <p className="eyebrow">Academic modules</p>
          <h2>Start with the area you need</h2>
        </section>

        <section className="module-grid">
          <Link className="module-card" to="/courses">
            <span>01</span>
            <strong>Courses</strong>
            <p>Browse course details, teachers, lectures and learning material.</p>
          </Link>
          <Link className="module-card" to="/internships">
            <span>02</span>
            <strong>Internships</strong>
            <p>Find practical learning opportunities and supporting resources.</p>
          </Link>
          <Link className="module-card" to="/books">
            <span>03</span>
            <strong>Books</strong>
            <p>Add and browse course books in a separate book-only module.</p>
          </Link>
          <Link className="module-card" to="/research">
            <span>04</span>
            <strong>Research</strong>
            <p>Review academic papers, publications and department research work.</p>
          </Link>
          <Link className="module-card" to="/about">
            <span>05</span>
            <strong>About OCW</strong>
            <p>Learn how the portal organizes academic information for students.</p>
          </Link>
        </section>

        {loading ? (
          <div className="loading-box">Loading featured content...</div>
        ) : (
          <>
            <section className="home-section-heading">
              <p className="eyebrow">Featured courses</p>
              <h2>Recently available courses</h2>
            </section>

            <section className="home-feature-grid">
              {featuredCourses.length ? (
                featuredCourses.map((course) => (
                  <article key={course.id} className="home-feature-card">
                    {course.thumbnail ? (
                      <img src={fileUrl(course.thumbnail)} alt="" />
                    ) : (
                      <div className="home-feature-placeholder">{course.title?.slice(0, 1) || 'C'}</div>
                    )}
                    <div>
                      <h3>{formatCourseTitle(course)}</h3>
                      <p>{course.short_description || course.description || 'Course details are available in the course catalog.'}</p>
                      <div className="home-card-meta">
                        <span>{course.instructor_name || 'Teacher not specified'}</span>
                        <span>{course.level || 'Level not specified'}</span>
                      </div>
                      <Link className="details-button" to={`/courses/${course.id}`}>Details</Link>
                    </div>
                  </article>
                ))
              ) : (
                <p className="empty-state">No courses are available yet.</p>
              )}
            </section>

            <section className="home-section-heading">
              <p className="eyebrow">Featured internships</p>
              <h2>Practical opportunities</h2>
            </section>

            <section className="home-feature-grid">
              {featuredInternships.length ? (
                featuredInternships.map((internship) => (
                  <article key={internship.id} className="home-feature-card">
                    {internship.thumbnail ? (
                      <img src={fileUrl(internship.thumbnail)} alt="" />
                    ) : (
                      <div className="home-feature-placeholder">{internship.title?.slice(0, 1) || 'I'}</div>
                    )}
                    <div>
                      <h3>{internship.title || 'Untitled internship'}</h3>
                      <p>{internship.description || 'Internship details are available in the internship catalog.'}</p>
                      <div className="home-card-meta">
                        <span>{internship.category || 'General'}</span>
                        <span>{internship.duration || 'Flexible duration'}</span>
                      </div>
                      <Link className="details-button" to={`/internships/${internship.id}`}>Details</Link>
                    </div>
                  </article>
                ))
              ) : (
                <p className="empty-state">No internships are available yet.</p>
              )}
            </section>

            <section className="home-cta-panel">
              <div>
                <p className="eyebrow">Keep exploring</p>
                <h2>Move from modules to complete academic details.</h2>
                <p>Use filters on the courses page to narrow content by faculty and department.</p>
              </div>
              <Link className="details-button" to="/courses">Open catalog</Link>
            </section>
          </>
        )}
      </div>
    </div>
  )
}

function formatCourseTitle(course) {
  const title = course.title || 'Untitled course'
  return course.course_code ? `${title} - ${course.course_code}` : title
}
