'use client'
import { motion } from 'framer-motion'
import { Users, Megaphone } from 'lucide-react'

const FacebookIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
  </svg>
)
const RedditIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
    <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z" />
  </svg>
)
const XIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
  </svg>
)
const InstagramIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
  </svg>
)
const YouTubeIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
    <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
  </svg>
)

// Set href to the real community URL to enable a card.
const PLATFORMS = [
  { name: 'Facebook',    icon: <FacebookIcon />,  href: null, desc: 'Follow our page for tips, updates, and fact-check highlights.' },
  { name: 'Reddit',      icon: <RedditIcon />,    href: null, desc: 'Join discussions and share suspicious articles for review.' },
  { name: 'X (Twitter)', icon: <XIcon />,         href: null, desc: 'Quick alerts on trending misinformation and new features.' },
  { name: 'Instagram',   icon: <InstagramIcon />, href: null, desc: 'Visual explainers on how to spot fake news.' },
  { name: 'YouTube',     icon: <YouTubeIcon />,   href: null, desc: 'Tutorials and deep dives into how the AI works.' },
]

const fadeUp = {
  hidden:  { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
}

const stagger = {
  visible: { transition: { staggerChildren: 0.12 } },
}

export default function CommunityPage() {
  return (
    <div className="min-h-screen pt-24 pb-20 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div variants={stagger} initial="hidden" animate="visible" className="text-center mb-16">
          <motion.div variants={fadeUp} className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-xs font-mono text-primary-600 dark:text-primary-300 mb-6">
            <Users className="w-3 h-3" /> Community
          </motion.div>
          <motion.h1 variants={fadeUp} className="text-4xl sm:text-5xl font-display font-800 text-ink mb-4">
            Join the <span className="text-gradient">Community</span>
          </motion.h1>
          <motion.p variants={fadeUp} className="text-ink/50 text-lg max-w-2xl mx-auto">
            Connect with Fake News Detector on social media — discuss trends, share verified sources, and help fight misinformation together.
          </motion.p>
        </motion.div>

        {/* Platform cards */}
        <motion.div variants={stagger} initial="hidden" animate="visible" className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
          {PLATFORMS.map((platform) => (
            platform.href ? (
              <motion.a
                key={platform.name}
                variants={fadeUp}
                href={platform.href}
                target="_blank"
                rel="noopener noreferrer"
                className="glass card-hover p-6 rounded-xl flex flex-col items-start gap-3"
              >
                <div className="w-12 h-12 rounded-xl bg-primary-500/10 text-primary-600 dark:text-primary-400 flex items-center justify-center">
                  {platform.icon}
                </div>
                <h3 className="font-display font-600 text-ink">{platform.name}</h3>
                <p className="text-ink/50 text-sm leading-relaxed">{platform.desc}</p>
              </motion.a>
            ) : (
              <motion.div
                key={platform.name}
                variants={fadeUp}
                aria-disabled="true"
                title="Coming soon"
                className="glass p-6 rounded-xl flex flex-col items-start gap-3 opacity-50 cursor-not-allowed select-none"
              >
                <div className="w-12 h-12 rounded-xl bg-ink/5 text-ink/40 flex items-center justify-center">
                  {platform.icon}
                </div>
                <div className="flex items-center gap-2">
                  <h3 className="font-display font-600 text-ink/60">{platform.name}</h3>
                  <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full bg-ink/5 text-ink/40 border border-ink/10">
                    Soon
                  </span>
                </div>
                <p className="text-ink/40 text-sm leading-relaxed">{platform.desc}</p>
              </motion.div>
            )
          ))}
        </motion.div>

        {/* Notice */}
        <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="glass p-4 rounded-xl flex items-center gap-3">
          <Megaphone className="w-5 h-5 text-primary-600 dark:text-primary-400 flex-shrink-0" />
          <p className="text-ink/40 text-xs">
            Our official social media communities are launching soon. Once they&apos;re live, the links above will be
            enabled — stay tuned!
          </p>
        </motion.div>
      </div>
    </div>
  )
}
