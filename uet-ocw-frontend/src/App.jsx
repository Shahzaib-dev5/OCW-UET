import { useEffect, useMemo, useState } from 'react'
import './App.css'
import FacultyList from './components/FacultyList'
import DepartmentList from './components/DepartmentList'
import DepartmentDetails from './components/DepartmentDetails'
import SelectedItemResources from './components/SelectedItemResources'
import { fetchJson } from './data/api'

function App() {
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [courses, setCourses] = useState([])
  const [internships, setInternships] = useState([])
  const [courseResources, setCourseResources] = useState([])
  const [internshipResources, setInternshipResources] = useState([])
  const [selectedFacultyId, setSelectedFacultyId] = useState(null)
  const [selectedDepartmentId, setSelectedDepartmentId] = useState(null)
  const [selectedCourseId, setSelectedCourseId] = useState(null)
  const [selectedInternshipId, setSelectedInternshipId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        setError('')

        const [facultiesData, departmentsData, coursesData, internshipsData, courseResourcesData, internshipResourcesData] = await Promise.all([
          fetchJson('/faculties'),
          fetchJson('/departments'),
          fetchJson('/courses'),
          fetchJson('/skills-development'),
          fetchJson('/course-resources'),
          fetchJson('/skills-development-resources'),
        ])

        setFaculties(facultiesData)
        setDepartments(departmentsData)
        setCourses(coursesData)
        setInternships(internshipsData)
        setCourseResources(courseResourcesData)
        setInternshipResources(internshipResourcesData)

        if (facultiesData[0]) {
          setSelectedFacultyId(facultiesData[0].id)
        }
      } catch (loadError) {
        setError(loadError.message || 'Unable to load UET data.')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  const facultyDepartments = useMemo(() => {
    if (!selectedFacultyId) return []
    return departments.filter((department) => String(department.faculty_id) === String(selectedFacultyId))
  }, [selectedFacultyId, departments])

  useEffect(() => {
    if (!facultyDepartments.length) {
      setSelectedDepartmentId(null)
      setSelectedCourseId(null)
      setSelectedInternshipId(null)
      return
    }

    if (!facultyDepartments.some((department) => String(department.id) === String(selectedDepartmentId))) {
      setSelectedDepartmentId(facultyDepartments[0].id)
    }
  }, [facultyDepartments, selectedDepartmentId])

  const selectedDepartment = useMemo(
    () => departments.find((department) => String(department.id) === String(selectedDepartmentId)) || null,
    [departments, selectedDepartmentId],
  )

  const departmentCourses = useMemo(
    () => courses.filter((course) => String(course.department_id) === String(selectedDepartmentId)),
    [courses, selectedDepartmentId],
  )

  const departmentInternships = useMemo(
    () => internships.filter((internship) => String(internship.department_id) === String(selectedDepartmentId)),
    [internships, selectedDepartmentId],
  )

  useEffect(() => {
    if (selectedDepartmentId == null) {
      setSelectedCourseId(null)
      setSelectedInternshipId(null)
      return
    }

    const courseExists = departmentCourses.some((course) => String(course.id) === String(selectedCourseId))
    const internshipExists = departmentInternships.some((internship) => String(internship.id) === String(selectedInternshipId))

    if (!courseExists && departmentCourses.length) {
      setSelectedCourseId(departmentCourses[0].id)
    }
    if (!internshipExists && departmentInternships.length) {
      setSelectedInternshipId(departmentInternships[0].id)
    }
  }, [departmentCourses, departmentInternships, selectedCourseId, selectedDepartmentId, selectedInternshipId])

  const selectedCourse = useMemo(
    () => courses.find((course) => String(course.id) === String(selectedCourseId)) || null,
    [courses, selectedCourseId],
  )

  const selectedInternship = useMemo(
    () => internships.find((internship) => String(internship.id) === String(selectedInternshipId)) || null,
    [internships, selectedInternshipId],
  )

  const selectedCourseResources = useMemo(
    () => courseResources.filter((resource) => String(resource.course_id) === String(selectedCourseId)),
    [courseResources, selectedCourseId],
  )

  const selectedInternshipResources = useMemo(
    () => internshipResources.filter((resource) => String(resource.internship_id) === String(selectedInternshipId)),
    [internshipResources, selectedInternshipId],
  )

  const selectedFaculty = useMemo(
    () => faculties.find((faculty) => String(faculty.id) === String(selectedFacultyId)) || null,
    [faculties, selectedFacultyId],
  )

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-badge">UET</div>
          <div>
            <p className="eyebrow">University of Engineering & Technology</p>
            <h1>Courseware</h1>
          </div>
        </div>
      </header>

      <main className="page">
        {error && <div className="alert-box">{error}</div>}

        {loading ? (
          <div className="loading-box">Loading UET content...</div>
        ) : (
          <div className="content-flow">
            <FacultyList
              faculties={faculties}
              selectedFacultyId={selectedFacultyId}
              onSelectFaculty={(facultyId) => {
                setSelectedFacultyId(facultyId)
                setSelectedDepartmentId(null)
                setSelectedCourseId(null)
                setSelectedInternshipId(null)
              }}
            />

            {selectedFaculty && (
              <DepartmentList
                departments={facultyDepartments}
                selectedDepartmentId={selectedDepartmentId}
                onSelectDepartment={(departmentId) => {
                  setSelectedDepartmentId(departmentId)
                  setSelectedCourseId(null)
                  setSelectedInternshipId(null)
                }}
              />
            )}

            {selectedDepartment && (
              <DepartmentDetails
                department={selectedDepartment}
                courses={departmentCourses}
                internships={departmentInternships}
                selectedCourseId={selectedCourseId}
                selectedInternshipId={selectedInternshipId}
                onSelectCourse={(courseId) => {
                  setSelectedCourseId(courseId)
                  setSelectedInternshipId(null)
                }}
                onSelectInternship={(internshipId) => {
                  setSelectedInternshipId(internshipId)
                  setSelectedCourseId(null)
                }}
              />
            )}

            {selectedCourse && (
              <SelectedItemResources
                title={selectedCourse.title}
                description={selectedCourse.description || selectedCourse.short_description}
                items={selectedCourseResources}
                typeLabel="course"
              />
            )}

            {selectedInternship && (
              <SelectedItemResources
                title={selectedInternship.title}
                description={selectedInternship.description}
                items={selectedInternshipResources}
                typeLabel="skills development"
              />
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
