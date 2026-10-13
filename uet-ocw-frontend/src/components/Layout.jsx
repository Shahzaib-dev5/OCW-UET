import { useEffect, useRef, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import uetLogo from '../assets/uet-logo.png'

export default function Layout({ children }) {
  const year = new Date().getFullYear()
  const { user, logout, isApprovedInstructor, isInstructorMode, setViewMode, isAdmin } = useAuth()
  const displayName = user?.full_name || user?.username || user?.email || 'Profile'
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false)
  const profileMenuRef = useRef(null)
  const avatarInitial = displayName.trim().charAt(0).toUpperCase() || 'U'
  const navItems = [
    { to: '/', label: 'Home' },
    { to: '/about', label: 'About' },
    { to: '/courses', label: 'Courses' },
    { to: '/books', label: 'Books' },
    { to: '/skills-development', label: 'Skills Development' },
    { to: '/invited-talks', label: 'Tech Talks' },
    //{ to: '/research', label: 'Research' },
  ]

  const switchViewMode = () => {
    const nextMode = isInstructorMode ? 'student' : 'instructor'
    setViewMode(nextMode)
    setIsMenuOpen(false)
  }

  const closeMenus = () => {
    setIsMenuOpen(false)
    setIsProfileMenuOpen(false)
  }

  const handleLogout = () => {
    logout()
    closeMenus()
  }

  useEffect(() => {
    if (!isProfileMenuOpen) return undefined

    const handlePointerDown = (event) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
        setIsProfileMenuOpen(false)
      }
    }

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setIsProfileMenuOpen(false)
      }
    }

    document.addEventListener('pointerdown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isProfileMenuOpen])

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
                onClick={closeMenus}
              >
                {item.label}
              </NavLink>
            ))}
            {isApprovedInstructor && (
              <button
                type="button"
                className={isInstructorMode ? 'nav-mode-toggle instructor' : 'nav-mode-toggle'}
                aria-pressed={isInstructorMode}
                onClick={switchViewMode}
              >
                <span aria-hidden="true" />
                {isInstructorMode ? 'Instructor UI' : 'Student UI'}
              </button>
            )}
            {isAdmin && (
              <NavLink to="/admin" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')} onClick={closeMenus}>
                Admin
              </NavLink>
            )}
            {user ? (
              <div className="profile-menu" ref={profileMenuRef}>
                <button
                  type="button"
                  className="profile-avatar-button"
                  aria-label={`${displayName} account menu`}
                  aria-haspopup="menu"
                  aria-expanded={isProfileMenuOpen}
                  onClick={() => setIsProfileMenuOpen((current) => !current)}
                >
                  <span aria-hidden="true">{avatarInitial}</span>
                </button>
                {isProfileMenuOpen && (
                  <div className="profile-dropdown" role="menu">
                    <NavLink to="/account" className="profile-dropdown-item" role="menuitem" onClick={closeMenus}>
                      Profile
                    </NavLink>
                    <button type="button" className="profile-dropdown-item" role="menuitem" onClick={handleLogout}>
                      Logout
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <NavLink to="/login" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')} onClick={closeMenus}>
                Login
              </NavLink>
            )}
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
              Explore course material, skills development resources, and tech talks from University of
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
