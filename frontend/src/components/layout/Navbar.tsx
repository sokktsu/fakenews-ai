'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Menu, X } from 'lucide-react'
import ThemeToggle from './ThemeToggle'

const NAV_LINKS = [
  { href: '/about',          label: 'About' },
  { href: '/resources',      label: 'Resources' },
  { href: '/community',      label: 'Community' },
  { href: '/team',           label: 'Team' },
  { href: '/contact',        label: 'Contact', disabled: true },  // set disabled: false to re-enable
]

export default function Navbar() {
  const [open, setOpen] = useState(false)
  const pathname = usePathname()

  useEffect(() => { setOpen(false) }, [pathname])

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-card/90 backdrop-blur border-b border-ink/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Wordmark (home link) */}
          <Link href="/" className="font-display font-700 text-sm text-ink">
            Fake News Detector
          </Link>

          {/* Desktop nav — right aligned */}
          <div className="hidden lg:flex items-center gap-1">
            <nav className="flex items-center">
              {NAV_LINKS.map((link) => (
                link.disabled ? (
                  <span
                    key={link.href}
                    aria-disabled="true"
                    title="Coming soon"
                    className="px-3 py-2 rounded-md text-sm text-ink/25 cursor-not-allowed select-none"
                  >
                    {link.label}
                  </span>
                ) : (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`px-3 py-2 rounded-md text-sm transition-colors ${
                      pathname === link.href
                        ? 'text-ink font-semibold'
                        : 'text-ink/60 hover:text-ink'
                    }`}
                  >
                    {link.label}
                  </Link>
                )
              ))}
            </nav>
            <ThemeToggle />
          </div>

          {/* Mobile */}
          <div className="lg:hidden flex items-center gap-1">
            <ThemeToggle />
            <button
              className="p-2 rounded-lg text-ink/70 hover:text-ink hover:bg-ink/5 transition-colors"
              onClick={() => setOpen(!open)}
              aria-label="Toggle menu"
            >
              {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="lg:hidden bg-card border-t border-ink/10">
          <div className="px-4 py-3 space-y-1">
            {NAV_LINKS.map((link) => (
              link.disabled ? (
                <span
                  key={link.href}
                  aria-disabled="true"
                  className="block px-4 py-2.5 rounded-md text-sm text-ink/25 cursor-not-allowed select-none"
                >
                  {link.label}
                </span>
              ) : (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`block px-4 py-2.5 rounded-md text-sm transition-colors ${
                    pathname === link.href
                      ? 'text-ink font-semibold bg-ink/5'
                      : 'text-ink/60 hover:text-ink hover:bg-ink/5'
                  }`}
                >
                  {link.label}
                </Link>
              )
            ))}
          </div>
        </div>
      )}
    </header>
  )
}
