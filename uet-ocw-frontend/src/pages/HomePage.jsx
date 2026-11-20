import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import TitleImageFallback from '../components/TitleImageFallback'
import { fetchJson, fileUrl } from '../data/api'
import uetLogo from '../assets/uet-logo.png'
import kicsLogo from '../assets/kics-logo.png'
import ulefLogo from '../assets/ulef-logo.png'

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
          fetchJson('/skills-development'),
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
            <p className="home-hero-label">UET Lahore Open Courseware</p>
            <h2>Knowledge, openly shared.</h2>
            <p>
              Learn beyond the classroom with open courses, books, technical talks and practical development pathways from UET Lahore.
            </p>
            <div className="home-hero-actions">
              <Link className="primary-button" to="/courses">Explore Courses</Link>
              <Link className="secondary-button light" to="/books">Browse the Library</Link>
            </div>
          </div>
          <aside className="home-hero-note" aria-label="Open learning commitment">
            <span>Open access</span>
            <strong>Academic resources for every learner</strong>
            <p>Discover material organized by faculty, department and course.</p>
          </aside>
        </div>
      </section>

      <section className="institution-strip" aria-label="Open Courseware institutions">
        <div className="container institution-strip-inner">
          <div className="institution-copy">
            <p>Presented by</p>
            <strong>University expertise. Technology leadership. Learning uplift.</strong>
          </div>
          <div className="institution-logos">
            <div><img src={uetLogo} alt="UET Lahore logo" /><span>UET Lahore</span></div>
            <i aria-hidden="true" />
            <div><img src={kicsLogo} alt="KICS logo" /><span>KICS</span></div>
            <i aria-hidden="true" />
            <div className="institution-ulef"><img src={ulefLogo} alt="Uplift Learning and Education Foundation logo" /><span>Supported by ULEF</span></div>
          </div>
        </div>
      </section>

      <div className="container page-block">
        {error && <div className="alert-box">{error}</div>}

        <section className="home-section-heading">
          <p className="eyebrow">Explore open learning</p>
          <h2>Choose your way into the collection</h2>
          <p className="home-section-intro">From complete courses to focused reading and practical programs, find a path that fits what you want to learn.</p>
        </section>

        <section className="module-grid">
          <Link className="module-card" to="/courses">
            <span className="module-card-kicker">Learn</span>
            <strong>Courses</strong>
            <p>Browse course details, teachers, lectures and learning material.</p>
          </Link>
          <Link className="module-card" to="/skills-development">
            <span className="module-card-kicker">Practice</span>
            <strong>Skills Development</strong>
            <p>Find practical learning opportunities and supporting resources.</p>
          </Link>
          <Link className="module-card" to="/books">
            <span className="module-card-kicker">Read</span>
            <strong>Books</strong>
            <p>Browse course books and reading resources in a dedicated library.</p>
          </Link>
          <Link className="module-card" to="/research">
            <span className="module-card-kicker">Discover</span>
            <strong>Research</strong>
            <p>Review academic papers, publications and department research work.</p>
          </Link>
          <Link className="module-card" to="/about">
            <span className="module-card-kicker">Our mission</span>
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
                    <TitleImageFallback
                      className="home-feature-placeholder"
                      src={course.thumbnail ? fileUrl(course.thumbnail) : ''}
                      title={formatCourseTitle(course)}
                      label="Course"
                    />
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
              <p className="eyebrow">Featured skills development</p>
              <h2>Practical learning programs</h2>
            </section>

            <section className="home-feature-grid">
              {featuredInternships.length ? (
                featuredInternships.map((internship) => (
                  <article key={internship.id} className="home-feature-card">
                    <TitleImageFallback
                      className="home-feature-placeholder"
                      src={internship.thumbnail ? fileUrl(internship.thumbnail) : ''}
                      title={internship.title || 'Skills Development'}
                      label="Skills Development"
                    />
                    <div>
                      <h3>{internship.title || 'Untitled skills development program'}</h3>
                      <p>{internship.description || 'Skills development details are available in the catalog.'}</p>
                      <div className="home-card-meta">
                        <span>{internship.category || 'General'}</span>
                        <span>{internship.duration || 'Flexible duration'}</span>
                      </div>
                      <Link className="details-button" to={`/skills-development/${internship.id}`}>Details</Link>
                    </div>
                  </article>
                ))
              ) : (
                <p className="empty-state">No skills development programs are available yet.</p>
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
