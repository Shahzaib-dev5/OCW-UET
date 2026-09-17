import { NavLink } from 'react-router-dom'
import uetLogo from '../assets/uet-logo.png'

export default function Layout({ children }) {
  const navItems = [
    { to: '/', label: 'Home' },
    { to: '/about', label: 'About' },
    { to: '/courses', label: 'Course' },
    { to: '/internships', label: 'Internship' },
    { to: '/research', label: 'Research' },
  ]

  return (
    <div className="site-shell">
      <header className="site-header">
        <div className="container nav-bar">
          <div className="brand-wrap">
            <img className="brand-mark" src={uetLogo} alt="UET Lahore logo" />
            <div>
              <p className="brand-tag">University</p>
              <h1>Open Courseware</h1>
            </div>
          </div>

          <nav className="main-nav" aria-label="Main navigation">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main>{children}</main>
    </div>
  )
}
