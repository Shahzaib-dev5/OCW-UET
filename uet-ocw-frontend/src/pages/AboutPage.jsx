import { Link } from 'react-router-dom'

export default function AboutPage() {
  return (
    <div className="about-page">
      <section className="about-hero-banner">
        <div className="container">
          <div className="about-hero-content">
            <p className="eyebrow">About UET OCW</p>
            <h2>Academic access designed around students.</h2>
            <p>
              UET Open Courseware brings courses, lecture material, tech talks and skills development opportunities into one organized experience.
            </p>
          </div>
        </div>
      </section>

      <div className="container page-block">
        <section className="about-story-panel">
          <div>
            <p className="eyebrow">Our purpose</p>
            <h2>Make university learning resources easier to find, understand and use.</h2>
          </div>
          <p>
            The portal connects academic content with the structure students already know: faculties, departments, courses and opportunities. It keeps important details close together so a learner can move from overview to resource without getting lost.
          </p>
        </section>

        <section className="about-value-grid">
          <article>
            <span>01</span>
            <h3>Courses</h3>
            <p>Browse teacher information, course outlines, credit details, lecture lists and learning material.</p>
          </article>
          <article>
            <span>02</span>
            <h3>Research</h3>
            <p>Explore academic work and publication details connected with university departments.</p>
          </article>
          <article>
            <span>03</span>
            <h3>Skills Development</h3>
            <p>Find practical opportunities, supporting files and career-focused learning resources.</p>
          </article>
        </section>

        <section className="about-flow-panel">
          <div className="about-flow-item">
            <strong>Discover</strong>
            <p>Start from a module such as courses, tech talks or skills development.</p>
          </div>
          <div className="about-flow-item">
            <strong>Filter</strong>
            <p>Narrow content by faculty, department and available academic records.</p>
          </div>
          <div className="about-flow-item">
            <strong>Learn</strong>
            <p>Open details, lectures, resources and links prepared for student use.</p>
          </div>
        </section>

        <section className="about-cta-panel">
          <div>
            <p className="eyebrow">Start exploring</p>
            <h2>Go directly to the academic catalog.</h2>
            <p>Courses are organized with filters so students can quickly reach the right department and subject.</p>
          </div>
          <div className="about-cta-actions">
            <Link className="details-button" to="/courses">Courses</Link>
            <Link className="details-button secondary-flat" to="/research">Research</Link>
          </div>
        </section>
      </div>
    </div>
  )
}
