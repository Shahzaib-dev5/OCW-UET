import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchJson, fileNameFromUrl, fileUrl } from '../data/api'

const menuItems = [
  { href: '#introduction', label: 'Introduction' },
  { href: '#syllabus', label: 'Syllabus' },
  { href: '#calendar', label: 'Calendar' },
  { href: '#materials', label: 'Material/Videos' },
  { href: '#reading', label: 'Reading' },
  { href: '#online-resources', label: 'Online Resources' },
]

export default function CourseDetailPage() {
  const { courseId } = useParams()
  const [course, setCourse] = useState(null)
  const [resources, setResources] = useState([])
  const [lectures, setLectures] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadCourse() {
      try {
        setLoading(true)
        setError('')

        const [courseData, resourceData, lectureData] = await Promise.all([
          fetchJson(`/courses/${courseId}`),
          fetchJson(`/course-resources/course/${courseId}`),
          fetchJson(`/lectures/course/${courseId}`),
        ])

        setCourse(courseData)
        setResources(resourceData)
        setLectures(lectureData)
      } catch (loadError) {
        setError(loadError.message || 'Unable to load course details.')
      } finally {
        setLoading(false)
      }
    }

    loadCourse()
  }, [courseId])

  const readingResources = useMemo(
    () => resources.filter((resource) => /book|read|pdf|note|document/i.test(`${resource.resource_type} ${resource.title}`)),
    [resources],
  )

  const onlineResources = useMemo(
    () => resources.filter((resource) => resource.external_url || !readingResources.includes(resource)),
    [resources, readingResources],
  )

  if (loading) {
    return <div className="container page-block"><div className="loading-box">Loading course details...</div></div>
  }

  if (error) {
    return (
      <div className="container page-block">
        <div className="alert-box">{error}</div>
        <Link to="/courses" className="primary-button small">Back to courses</Link>
      </div>
    )
  }

  if (!course) {
    return (
      <div className="container page-block">
        <div className="content-panel">
          <p className="eyebrow">Course not found</p>
          <h2>We could not find this course.</h2>
          <Link to="/courses" className="primary-button small">Back to courses</Link>
        </div>
      </div>
    )
  }

  const creditHours = course.credit_hours ? `${course.credit_hours}` : 'Not specified'
  const duration = course.duration || formatLectureCount(lectures.length)
  const aboutText = course.description || course.short_description || 'Course details are available from the backend.'

  return (
    <div className="course-detail-page">
      <section className="course-detail-hero">
        <div className="container course-detail-hero-inner">
          {course.thumbnail ? (
            <img className="course-detail-thumb" src={fileUrl(course.thumbnail)} alt="" />
          ) : (
            <div className="course-detail-thumb placeholder">{course.title?.slice(0, 1) || 'C'}</div>
          )}

          <div className="course-detail-summary">
            <h2>{formatCourseTitle(course)}</h2>
            <div className="course-detail-facts">
              <div className="mini-fact teacher-fact">
                <span className="teacher-avatar">{initials(course.instructor_name)}</span>
                <div>
                  <small>Teacher</small>
                  <strong>{course.instructor_name || 'Teacher not specified'}</strong>
                </div>
              </div>
              <div className="mini-fact">
                <small>Category</small>
                <strong>{course.category || course.department?.name || 'General'}</strong>
              </div>
              <div className="mini-fact">
                <small>Duration</small>
                <strong>{duration}</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="container course-detail-layout">
        <aside className="course-menu" aria-label="Course menu">
          <h3>Course Menu</h3>
          {menuItems.map((item) => (
            <a key={item.href} href={item.href}>{item.label}</a>
          ))}
        </aside>

        <main className="course-detail-content">
          <section id="introduction" className="course-section">
            <h3>Course Introduction</h3>
            <div className="course-intro-grid">
              <table className="highlight-table">
                <tbody>
                  <tr>
                    <th colSpan="2">Course Highlight</th>
                  </tr>
                  <tr>
                    <td>Level</td>
                    <td>{course.level || 'Not specified'}</td>
                  </tr>
                  <tr>
                    <td>Credit Hours</td>
                    <td>{creditHours}</td>
                  </tr>
                  <tr>
                    <td>Lessons</td>
                    <td>{lectures.length}</td>
                  </tr>
                  <tr>
                    <td>Type</td>
                    <td>{course.course_type || 'Hybrid'}</td>
                  </tr>
                </tbody>
              </table>

              <div className="about-course">
                <h4>About The Course</h4>
                <p>{aboutText}</p>
              </div>
            </div>
          </section>

          <section id="syllabus" className="course-section">
            <h3>Syllabus</h3>
            <div className="section-rule" />
            <p className="section-copy">{course.syllabus || course.short_description || 'Syllabus details can be added from the admin course form.'}</p>
          </section>

          <section id="calendar" className="course-section">
            <h3>Course Calendar</h3>
            <table className="course-calendar-table">
              <thead>
                <tr>
                  <th>Lecture</th>
                  <th>Topics</th>
                </tr>
              </thead>
              <tbody>
                {lectures.length ? (
                  lectures.map((lecture) => (
                    <tr key={lecture.id}>
                      <td>{lecture.lecture_number}</td>
                      <td>{lecture.title}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="2">No lectures are available yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>

          <section id="materials" className="course-section">
            <h3>Course Material/Videos</h3>
            <table className="course-resource-table">
              <thead>
                <tr>
                  <th>Available Resources</th>
                  <th>Links</th>
                </tr>
              </thead>
              <tbody>
                {lectures.length ? (
                  lectures.map((lecture) => (
                    <tr key={lecture.id}>
                      <td>
                        <strong>Lecture {lecture.lecture_number}</strong>
                        {' - '}
                        {lecture.title}
                      </td>
                      <td>
                        <LectureLink href={lecture.video_url} label="video" />
                        <LectureLink href={lecture.presentation_url} label="ppt" />
                        <LectureLink href={lecture.notes_url} label="pdf" />
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="2">No lecture material is available yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>

          <section id="reading" className="course-section">
            <h3>Reading</h3>
            <ResourceRows resources={readingResources} emptyText="No reading resources are available yet." />
          </section>

          <section id="online-resources" className="course-section">
            <h3>Online Resources</h3>
            <ResourceRows resources={onlineResources} emptyText="No online resources are available yet." />
          </section>
        </main>
      </div>
    </div>
  )
}

function LectureLink({ href, label }) {
  if (!href) return <span className="muted-resource">{label}</span>
  return <a href={fileUrl(href)} target="_blank" rel="noreferrer">{label}</a>
}

function ResourceRows({ resources, emptyText }) {
  if (!resources.length) return <p className="empty-state">{emptyText}</p>

  return (
    <table className="course-resource-table">
      <tbody>
        {resources.map((resource) => (
          <tr key={resource.id}>
            <td>
              <strong>{resource.title}</strong>
              {resource.description && <span>{resource.description}</span>}
            </td>
            <td>
              {resource.external_url && <a href={fileUrl(resource.external_url)} target="_blank" rel="noreferrer">link</a>}
              {resource.file_url && (
                <>
                  <a href={fileUrl(resource.file_url)} target="_blank" rel="noreferrer">view</a>
                  <a href={fileUrl(resource.file_url)} download={fileNameFromUrl(resource.file_url, resource.title)}>download</a>
                </>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function formatCourseTitle(course) {
  const title = course.title || 'Untitled course'
  return course.course_code ? `${title} - ${course.course_code}` : title
}

function formatLectureCount(count = 0) {
  return `${count} ${count === 1 ? 'Lecture' : 'Lectures'}`
}

function initials(name) {
  const value = String(name || '').trim()
  if (!value) return 'T'
  return value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}
