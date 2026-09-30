import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { fetchJson, fileUrl } from '../data/api'

export default function CoursePage() {
  const navigate = useNavigate()
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [courses, setCourses] = useState([])
  const [lectureCounts, setLectureCounts] = useState({})
  const [selectedFacultyId, setSelectedFacultyId] = useState(null)
  const [selectedDepartmentId, setSelectedDepartmentId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        setError('')
        const [facultiesData, departmentsData, coursesData, lecturesData] = await Promise.all([
          fetchJson('/faculties'),
          fetchJson('/departments'),
          fetchJson('/courses'),
          fetchJson('/lectures'),
        ])

        setFaculties(facultiesData)
        setDepartments(departmentsData)
        setCourses(coursesData)
        setLectureCounts(countLecturesByCourse(lecturesData))

      } catch (loadError) {
        setError(loadError.message || 'Unable to load course information.')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  const facultyDepartments = useMemo(() => {
    if (!selectedFacultyId) return departments
    return departments.filter((department) => String(department.faculty_id) === String(selectedFacultyId))
  }, [departments, selectedFacultyId])

  useEffect(() => {
    if (!selectedFacultyId || !facultyDepartments.length) {
      setSelectedDepartmentId(null)
      return
    }

    if (!facultyDepartments.some((department) => String(department.id) === String(selectedDepartmentId))) {
      setSelectedDepartmentId(null)
    }
  }, [facultyDepartments, selectedDepartmentId, selectedFacultyId])

  const filteredCourses = useMemo(() => {
    if (selectedDepartmentId) {
      return courses.filter((course) => String(course.department_id) === String(selectedDepartmentId))
    }

    if (selectedFacultyId) {
      const departmentIds = new Set(facultyDepartments.map((department) => String(department.id)))
      return courses.filter((course) => departmentIds.has(String(course.department_id)))
    }

    return courses
  }, [courses, facultyDepartments, selectedDepartmentId, selectedFacultyId])

  return (
    <div className="course-page">
      <section className="course-title-band">
        <div className="container">
          <h2>Courses</h2>
          <div className="breadcrumb-line">
            <Link to="/">Home</Link>
            <span>/</span>
            <span>Hybrid Courses</span>
          </div>
        </div>
      </section>

      <div className="container page-block">
        {error && <div className="alert-box">{error}</div>}

        {loading ? (
          <div className="loading-box">Loading courses...</div>
        ) : (
          <>
            <section className="course-filters">
              <label className="field-label">
                Faculty
                <select
                  value={selectedFacultyId || ''}
                  onChange={(event) => {
                    setSelectedFacultyId(event.target.value)
                    setSelectedDepartmentId(null)
                  }}
                >
                  <option value="">All faculties</option>
                  {faculties.map((faculty) => (
                    <option key={faculty.id} value={faculty.id}>
                      {faculty.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field-label">
                Department
                <select
                  value={selectedDepartmentId || ''}
                  onChange={(event) => {
                    setSelectedDepartmentId(event.target.value)
                  }}
                >
                  <option value="">All departments</option>
                  {facultyDepartments.map((department) => (
                    <option key={department.id} value={department.id}>
                      {department.name}
                    </option>
                  ))}
                </select>
              </label>
            </section>

            <section className="course-list-panel">
              {filteredCourses.length ? (
                filteredCourses.map((course) => (
                  <article key={course.id} className="course-list-card">
                    {course.thumbnail ? (
                      <img className="course-list-media" src={fileUrl(course.thumbnail)} alt="" />
                    ) : (
                      <div className="course-list-media placeholder">{course.title?.slice(0, 1) || 'C'}</div>
                    )}

                    <div className="course-list-body">
                      <h3>{formatCourseTitle(course)}</h3>
                      <div className="teacher-strip">
                        <span className="teacher-avatar">{initials(course.instructor_name)}</span>
                        <span>{course.instructor_name || 'Teacher not specified'}</span>
                      </div>
                      <p>{course.short_description || course.description || 'Course details are available in the backend data.'}</p>
                      <div className="course-list-footer">
                        <div className="course-stats" aria-label="Course facts">
                          <span>{formatLectureCount(lectureCounts[course.id])}</span>
                          <span>{course.credit_hours || course.credits || course.semester || 'Credit hours not specified'}</span>
                          <span>{course.level || 'Level not specified'}</span>
                        </div>
                        <button
                          type="button"
                          className="details-button"
                          onClick={() => navigate(`/courses/${course.id}`)}
                        >
                          Details
                        </button>
                      </div>
                    </div>
                  </article>
                ))
              ) : (
                <p className="empty-state">No courses are available for the selected filters yet.</p>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  )
}

function countLecturesByCourse(lectures) {
  return lectures.reduce((counts, lecture) => {
    counts[lecture.course_id] = (counts[lecture.course_id] || 0) + 1
    return counts
  }, {})
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
