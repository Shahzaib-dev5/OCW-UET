import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { fetchJson, fileUrl } from '../data/api'

export default function CoursePage() {
  const navigate = useNavigate()
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [courses, setCourses] = useState([])
  const [selectedFacultyId, setSelectedFacultyId] = useState(null)
  const [selectedDepartmentId, setSelectedDepartmentId] = useState(null)
  const [selectedCourseId, setSelectedCourseId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        const [facultiesData, departmentsData, coursesData] = await Promise.all([
          fetchJson('/faculties'),
          fetchJson('/departments'),
          fetchJson('/courses'),
        ])

        setFaculties(facultiesData)
        setDepartments(departmentsData)
        setCourses(coursesData)

        if (facultiesData[0]) {
          setSelectedFacultyId(facultiesData[0].id)
        }
      } catch (loadError) {
        setError(loadError.message || 'Unable to load course information.')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  const facultyDepartments = useMemo(() => {
    if (!selectedFacultyId) return []
    return departments.filter((department) => String(department.faculty_id) === String(selectedFacultyId))
  }, [departments, selectedFacultyId])

  useEffect(() => {
    if (!facultyDepartments.length) {
      setSelectedDepartmentId(null)
      return
    }

    if (!facultyDepartments.some((department) => String(department.id) === String(selectedDepartmentId))) {
      setSelectedDepartmentId(facultyDepartments[0].id)
    }
  }, [facultyDepartments, selectedDepartmentId])

  const departmentCourses = useMemo(() => {
    if (!selectedDepartmentId) return []
    return courses.filter((course) => String(course.department_id) === String(selectedDepartmentId))
  }, [courses, selectedDepartmentId])

  useEffect(() => {
    if (!departmentCourses.length) {
      setSelectedCourseId(null)
      return
    }

    if (!departmentCourses.some((course) => String(course.id) === String(selectedCourseId))) {
      setSelectedCourseId(departmentCourses[0].id)
    }
  }, [departmentCourses, selectedCourseId])

  const selectedCourse = useMemo(
    () => departmentCourses.find((course) => String(course.id) === String(selectedCourseId)) || null,
    [departmentCourses, selectedCourseId],
  )

  return (
    <div className="container page-block">
      <section className="content-panel">
        <p className="eyebrow">Course catalog</p>
        <h2>Choose a faculty and department</h2>
      </section>

      {error && <div className="alert-box">{error}</div>}

      {loading ? (
        <div className="loading-box">Loading courses...</div>
      ) : (
        <>
          <section className="content-panel catalog-filters">
            <label className="field-label">
              Faculty
              <select
                value={selectedFacultyId || ''}
                onChange={(event) => {
                  setSelectedFacultyId(event.target.value)
                  setSelectedDepartmentId(null)
                  setSelectedCourseId(null)
                }}
              >
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
                  setSelectedCourseId(null)
                }}
              >
                {facultyDepartments.map((department) => (
                  <option key={department.id} value={department.id}>
                    {department.name}
                  </option>
                ))}
              </select>
            </label>
          </section>

          <section className="catalog-results">
            <div className="section-heading-row">
              <h3>Courses</h3>
              <span>{departmentCourses.length} available</span>
            </div>
            <div className="card-grid catalog-grid">
              {departmentCourses.map((course) => (
                <article
                  key={course.id}
                  className={String(selectedCourseId) === String(course.id) ? 'catalog-card selected' : 'catalog-card'}
                >
                  {course.thumbnail ? (
                    <img className="catalog-card-media" src={fileUrl(course.thumbnail)} alt="" />
                  ) : (
                    <div className="catalog-card-media placeholder">{course.title?.slice(0, 1) || 'C'}</div>
                  )}
                  <button
                    type="button"
                    className="catalog-card-button"
                    onClick={() => setSelectedCourseId(course.id)}
                  >
                    <strong>{course.title}</strong>
                    <span>{course.course_code || course.level || 'Course'}</span>
                  </button>
                  <button
                    type="button"
                    className="read-more-button"
                    onClick={() => navigate(`/courses/${course.id}`)}
                  >
                    Read more
                  </button>
                </article>
              ))}
            </div>
          </section>
        </>
      )}

      {selectedCourse && (
        <section className="content-panel detail-panel">
          <p className="eyebrow">Selected course</p>
          <h3>{selectedCourse.title}</h3>
          <p>{selectedCourse.short_description || selectedCourse.description || 'Course details are available in the backend data.'}</p>
          <div className="meta-row">
            <span>{selectedCourse.course_code || 'No code'}</span>
            <span>{selectedCourse.level || 'Level not specified'}</span>
            <span>{selectedCourse.semester || 'Semester not specified'}</span>
          </div>

          <Link to={`/courses/${selectedCourse.id}`} className="primary-button small">Read more</Link>
        </section>
      )}
    </div>
  )
}
