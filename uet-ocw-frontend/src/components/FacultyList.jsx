export default function FacultyList({ faculties, selectedFacultyId, onSelectFaculty }) {
  return (
    <section className="panel block">
      <div className="panel-header-row">
        <h2>Faculties</h2>
      </div>

      <div className="stack-buttons">
        {faculties.map((faculty) => (
          <button
            key={faculty.id}
            type="button"
            className={selectedFacultyId === faculty.id ? 'option-button active' : 'option-button'}
            onClick={() => onSelectFaculty(faculty.id)}
          >
            <span>{faculty.name}</span>
            <small>{faculty.short_name || 'Faculty'}</small>
          </button>
        ))}
      </div>
    </section>
  )
}
