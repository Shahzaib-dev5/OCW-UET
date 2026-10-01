import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import TitleImageFallback from '../components/TitleImageFallback'
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
  const [shareStatus, setShareStatus] = useState('')
  const shareTimerRef = useRef(null)

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

  useEffect(() => () => {
    if (shareTimerRef.current) window.clearTimeout(shareTimerRef.current)
  }, [])

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

  const creditHours = course.credit_hours ? `${course.credit_hours} CH` : 'Not set'
  const aboutText = course.description || course.short_description || 'Course details are available from the backend.'
  const category = course.category || course.department?.name || 'General'
  const courseType = getCourseType(course)
  const courseLevel = titleCaseText(course.level || 'Not specified')
  const summary = getCourseSummary(course)

  const handleShare = async () => {
    const shareData = {
      title: formatCourseTitle(course),
      text: summary || aboutText,
      url: window.location.href,
    }

    try {
      if (navigator.share) {
        await navigator.share(shareData)
        return
      }

      await navigator.clipboard.writeText(window.location.href)
      setShareStatus('Link copied')
      if (shareTimerRef.current) window.clearTimeout(shareTimerRef.current)
      shareTimerRef.current = window.setTimeout(() => setShareStatus(''), 1800)
    } catch {
      setShareStatus('Unable to share')
      if (shareTimerRef.current) window.clearTimeout(shareTimerRef.current)
      shareTimerRef.current = window.setTimeout(() => setShareStatus(''), 1800)
    }
  }

  return (
    <div className="course-detail-page">
      <header className="course-detail-hero">
        <div className="container course-detail-hero-inner">
          <div className="course-detail-summary">
            <div className="course-detail-badges" aria-label="Course labels">
              <span>{courseType}</span>
              <span>{courseLevel}</span>
            </div>
            <h1>{formatCourseTitle(course)}</h1>
            {summary && <p className="course-detail-summary-text">{summary}</p>}
            <div className="course-detail-teacher">
              <div className="teacher-fact">
                <span className="teacher-avatar">{initials(course.instructor_name)}</span>
                <div>
                  <small>Teacher</small>
                  <strong>{course.instructor_name || 'Teacher not specified'}</strong>
                </div>
              </div>
            </div>
          </div>

          <aside className="course-quick-card" aria-label="Course quick facts and actions">
            <dl className="course-quick-facts">
              <div>
                <dt><Icon name="lectures" />Lectures</dt>
                <dd>{lectures.length}</dd>
              </div>
              <div>
                <dt><Icon name="lessons" />Lessons</dt>
                <dd>{resources.length}</dd>
              </div>
              <div>
                <dt><Icon name="credits" />Credit hours</dt>
                <dd className={!course.credit_hours ? 'muted-value' : ''}>{creditHours}</dd>
              </div>
              <div>
                <dt><Icon name="category" />Category</dt>
                <dd title={category}>{category}</dd>
              </div>
            </dl>

            <div className="course-quick-actions">
              <a className="course-start-button" href="#materials">Start learning</a>
              <div className="course-secondary-actions">
                <a href="#syllabus">Syllabus</a>
                <button type="button" onClick={handleShare}>Share</button>
              </div>
              {shareStatus && <p className="share-toast" role="status">{shareStatus}</p>}
            </div>
          </aside>
        </div>
      </header>

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
            <div className={course.thumbnail ? 'course-intro-grid' : 'course-intro-grid no-media'}>
              {course.thumbnail && (
                <figure className="course-intro-media">
                  <TitleImageFallback
                    className="course-intro-image"
                    src={course.thumbnail ? fileUrl(course.thumbnail) : ''}
                    alt={`${formatCourseTitle(course)} course poster`}
                    title={formatCourseTitle(course)}
                    label={courseType}
                  />
                </figure>
              )}
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

function Icon({ name }) {
  const paths = {
    lectures: 'M3 3.5h10v9H3z M5 6h6 M5 8h6 M5 10h3',
    lessons: 'M3 4h4.5A2.5 2.5 0 0 1 10 6.5V13a2.5 2.5 0 0 0-2.5-2.5H3z M10 6.5A2.5 2.5 0 0 1 12.5 4H13v6.5h-.5A2.5 2.5 0 0 0 10 13z',
    credits: 'M8 2.75 9.55 5.9l3.48.51-2.52 2.46.6 3.46L8 10.7l-3.11 1.63.6-3.46-2.52-2.46 3.48-.51z',
    category: 'M2.8 4.2h4.6l1 1.3h4.8v6.3H2.8z',
  }

  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false" className={`fact-icon ${name}`}>
      <path d={paths[name]} />
    </svg>
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

function getCourseType(course) {
  return titleCaseText(course.course_type || course.category || (course.semester ? 'Semester' : 'Hybrid'))
}

function getCourseSummary(course) {
  const value = String(course.short_description || course.description || '').trim()
  if (!value || value === 'Course details are available from the backend.') return ''
  return value
}

function titleCaseText(value) {
  return String(value || '')
    .trim()
    .replace(/[_-]+/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
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
