export default function HomePage() {
  return (
    <div className="container page-block">
      <section className="hero-section">
        <div className="hero-copy">
          <p className="eyebrow">Learn. Discover. Grow.</p>
          <h2>UET academic resources for future-ready students.</h2>
          <p>
            Explore faculties, departments, courses, internships and learning resources from the University of Engineering and Technology.
          </p>
          <div className="hero-actions">
            <a href="/courses" className="primary-button">Explore Courses</a>
            <a href="/internships" className="secondary-button">View Internships</a>
          </div>
        </div>

        <div className="hero-visual">
          <div className="stats-card">
            <span>Programs</span>
            <strong>Smart learning</strong>
          </div>
        </div>
      </section>
    </div>
  )
}
