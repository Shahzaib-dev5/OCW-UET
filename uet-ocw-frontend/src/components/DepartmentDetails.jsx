export default function DepartmentDetails({
  department,
  courses,
  internships,
  selectedCourseId,
  selectedInternshipId,
  onSelectCourse,
  onSelectInternship,
}) {
  return (
    <section className="panel block">
      <div className="department-header">
        <div>
          <p className="eyebrow">Selected department</p>
          <h2>{department.name}</h2>
        </div>
        <span className="pill">{department.department_type}</span>
      </div>

      <p className="department-description">
        {department.description || 'Department information from the UET backend.'}
      </p>

      <div className="grid-two">
        <div>
          <h3>Courses</h3>
          <div className="stack-buttons">
            {courses.map((course) => (
              <button
                key={course.id}
                type="button"
                className={selectedCourseId === course.id ? 'option-button active' : 'option-button'}
                onClick={() => onSelectCourse(course.id)}
              >
                <span>{course.title}</span>
                <small>{course.course_code || 'Course'}</small>
              </button>
            ))}
          </div>
        </div>

        <div>
          <h3>Skills Development</h3>
          <div className="stack-buttons">
            {internships.map((internship) => (
              <button
                key={internship.id}
                type="button"
                className={selectedInternshipId === internship.id ? 'option-button active' : 'option-button'}
                onClick={() => onSelectInternship(internship.id)}
              >
                <span>{internship.title}</span>
                <small>{internship.status || 'Open'}</small>
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
