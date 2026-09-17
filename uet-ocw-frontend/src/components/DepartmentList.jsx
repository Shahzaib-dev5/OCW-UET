export default function DepartmentList({ departments, selectedDepartmentId, onSelectDepartment }) {
  return (
    <section className="panel block">
      <div className="panel-header-row">
        <h2>Departments</h2>
      </div>

      <div className="stack-buttons">
        {departments.map((department) => (
          <button
            key={department.id}
            type="button"
            className={selectedDepartmentId === department.id ? 'option-button active' : 'option-button'}
            onClick={() => onSelectDepartment(department.id)}
          >
            <span>{department.name}</span>
            <small>{department.department_type}</small>
          </button>
        ))}
      </div>
    </section>
  )
}
