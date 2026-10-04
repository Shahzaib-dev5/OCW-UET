import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import uetLogo from '../assets/uet-logo.png'

export default function Layout({ children }) {
  const year = new Date().getFullYear()
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const navItems = [
    { to: '/', label: 'Home' },
    { to: '/about', label: 'About' },
    { to: '/courses', label: 'Courses' },
    { to: '/books', label: 'Books' },
    { to: '/skills-development', label: 'Skills Development' },
    { to: '/invited-talks', label: 'Invited Talks' },
    //{ to: '/research', label: 'Research' },
  ]

  return (
    <div className="site-shell">
      <header className="site-header">
        <div className="container nav-bar">
          <div className="brand-wrap">
            <img className="brand-mark" src={uetLogo} alt="UET Lahore logo" />
            <h1>Open Courseware</h1>
          </div>

          <button
            className="nav-toggle"
            type="button"
            aria-controls="main-navigation"
            aria-expanded={isMenuOpen}
            aria-label="Toggle navigation menu"
            onClick={() => setIsMenuOpen((current) => !current)}
          >
            <span aria-hidden="true" />
            <span aria-hidden="true" />
            <span aria-hidden="true" />
          </button>

          <nav
            id="main-navigation"
            className={isMenuOpen ? 'main-nav open' : 'main-nav'}
            aria-label="Main navigation"
          >
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
                onClick={() => setIsMenuOpen(false)}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main>{children}</main>

      <footer className="site-footer">
        <div className="container footer-main">
          <section className="footer-brand" aria-label="Open Courseware summary">
            <div className="footer-brand-head">
              <img className="footer-logo" src={uetLogo} alt="UET Lahore logo" />
              <div>
                <p className="footer-kicker">UET Lahore</p>
                <h2>Open Courseware</h2>
              </div>
            </div>
            <p>
              Explore course material, skills development resources, and invited talks from University of
              Engineering and Technology Lahore.
            </p>
          </section>

          <nav className="footer-links" aria-label="Footer navigation">
            <h3>Explore</h3>
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to}>
                {item.label}
              </NavLink>
            ))}
          </nav>

          <section className="footer-contact" aria-label="Contact information">
            <h3>Contact</h3>
            <p>University of Engineering and Technology</p>
            <p>G.T. Road, Lahore, Pakistan</p>
            <a href="mailto:info@uet.edu.pk">info@uet.edu.pk</a>
          </section>
        </div>

        <div className="footer-bottom">
          <div className="container footer-bottom-inner">
            <p>&copy; {year} UET Lahore Open Courseware. All rights reserved.</p>
            <a href="https://uet.edu.pk" target="_blank" rel="noreferrer">
              uet.edu.pk
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
