import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchJson, fileNameFromUrl, fileUrl } from '../data/api'

export default function CourseDetailPage() {
  const { courseId } = useParams()
  const [course, setCourse] = useState(null)
  const [resources, setResources] = useState([])
  const [lectures, setLectures] = useState([])
  const [activeTab, setActiveTab] = useState('overview')
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

  return (
    <div className="container page-block">
      <section className="content-panel detail-panel">
        <p className="eyebrow">Course details</p>
        <h2>{course.title}</h2>

        <div className="tab-row">
          <button type="button" className={activeTab === 'overview' ? 'tab-button active' : 'tab-button'} onClick={() => setActiveTab('overview')}>
            Overview
          </button>
          <button type="button" className={activeTab === 'lectures' ? 'tab-button active' : 'tab-button'} onClick={() => setActiveTab('lectures')}>
            Lectures ({lectures.length})
          </button>
          <button type="button" className={activeTab === 'resources' ? 'tab-button active' : 'tab-button'} onClick={() => setActiveTab('resources')}>
            Resources ({resources.length})
          </button>
        </div>

        {activeTab === 'overview' && (
          <>
            <p>{course.short_description || course.description || 'Course details are available from the backend.'}</p>
            <div className="meta-row">
              <span>{course.course_code || 'No code'}</span>
              <span>{course.level || 'Level not specified'}</span>
              <span>{course.semester || 'Semester not specified'}</span>
            </div>
          </>
        )}

        {activeTab === 'lectures' && (
          <div className="resource-list">
            <h3>All lectures</h3>
            {lectures.length ? (
              lectures.map((lecture) => (
                <div key={lecture.id} className="resource-item">
                  <strong>Lecture {lecture.lecture_number}: {lecture.title}</strong>
                  <span>{lecture.duration_minutes ? `${lecture.duration_minutes} minutes` : 'Duration not specified'}</span>
                  {lecture.description && <span>{lecture.description}</span>}
                  {lecture.video_url && (
                    <a href={fileUrl(lecture.video_url)} target="_blank" rel="noreferrer">Watch video</a>
                  )}
                  {lecture.notes_url && (
                    <a href={fileUrl(lecture.notes_url)} target="_blank" rel="noreferrer">Open notes</a>
                  )}
                  {lecture.presentation_url && (
                    <a href={fileUrl(lecture.presentation_url)} target="_blank" rel="noreferrer">Open slides</a>
                  )}
                </div>
              ))
            ) : (
              <p>No lectures are available for this course yet.</p>
            )}
          </div>
        )}

        {activeTab === 'resources' && (
          <div className="resource-list">
            <h3>Course resources</h3>
            {resources.length ? (
              resources.map((resource) => (
                <div key={resource.id} className="resource-item">
                  <strong>{resource.title}</strong>
                  <span>{resource.resource_type}</span>
                  {resource.description && <span>{resource.description}</span>}
                  {resource.external_url && (
                    <a href={fileUrl(resource.external_url)} target="_blank" rel="noreferrer">Open link</a>
                  )}
                  {resource.file_url && (
                    <div className="resource-links">
                      <a href={fileUrl(resource.file_url)} target="_blank" rel="noreferrer">View file</a>
                      <a href={fileUrl(resource.file_url)} download={fileNameFromUrl(resource.file_url, resource.title)}>
                        Download file
                      </a>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <p>No course resources are available for this course yet.</p>
            )}
          </div>
        )}

        <div className="hero-actions">
          <Link to="/courses" className="primary-button small">Back to courses</Link>
        </div>
      </section>
    </div>
  )
}
