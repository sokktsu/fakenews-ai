'use client'
import { motion } from 'framer-motion'
import { Users, GraduationCap, Linkedin, Github, Mail } from 'lucide-react'

const fadeUp = {
  hidden:  { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
}

const ADVISER = {
  name:  'Prof. [Adviser Name]',
  role:  'Thesis Adviser',
  dept:  'Department of Computer Science',
  avatar: '👨‍🏫',
  color:  'from-primary-500 to-primary-700',
}

const TEAM_MEMBERS = [
  {
    name:   '[Team Member 1]',
    avatar: '👨‍💻',
    color:  'from-accent-cyan to-teal-600',
    github: '#',
    linkedin: '#',
    email: '#',
  },
  {
    name:   '[Team Member 2]',
    avatar: '👩‍🎨',
    color:  'from-accent-magenta to-rose-600',
    github: '#',
    linkedin: '#',
    email: '#',
  },
  {
    name:   '[Team Member 3]',
    avatar: '👨‍🔬',
    color:  'from-amber-500 to-orange-600',
    github: '#',
    linkedin: '#',
    email: '#',
  },
]

export default function TeamPage() {
  return (
    <div className="min-h-screen pt-24 pb-20 px-4">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} className="text-center mb-14">
          <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-xs font-mono text-primary-600 dark:text-primary-300 mb-6">
            <Users className="w-3 h-3" /> The Research Team
          </div>
          <h1 className="text-4xl sm:text-5xl font-display font-800 text-ink mb-4">
            Meet the <span className="text-gradient">Team</span>
          </h1>
          <p className="text-ink/50 text-lg max-w-xl mx-auto">
            The researchers, developers, and mentors behind FakeNewsAI.
          </p>
        </motion.div>

        {/* Adviser */}
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="mb-12">
          <div className="flex items-center gap-3 mb-6">
            <GraduationCap className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            <h2 className="font-display font-700 text-ink text-xl">Thesis Adviser</h2>
          </div>
          <div className="glass-strong p-8 rounded-2xl flex flex-col sm:flex-row items-center sm:items-start gap-6">
            <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${ADVISER.color} flex items-center justify-center text-4xl flex-shrink-0`}>
              {ADVISER.avatar}
            </div>
            <div>
              <h3 className="font-display font-700 text-ink text-2xl mb-1">{ADVISER.name}</h3>
              <p className="text-primary-600 dark:text-primary-400 font-mono text-sm mb-1">{ADVISER.role}</p>
              <p className="text-ink/40 text-sm">{ADVISER.dept}</p>
            </div>
          </div>
        </motion.div>

        {/* Team members */}
        <div>
          <div className="flex items-center gap-3 mb-6">
            <Users className="w-5 h-5 text-accent-cyan" />
            <h2 className="font-display font-700 text-ink text-xl">Researchers</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {TEAM_MEMBERS.map((member, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass card-hover p-6 rounded-xl"
              >
                <div className="flex flex-col items-center text-center gap-4">
                  <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${member.color} flex items-center justify-center text-2xl flex-shrink-0`}>
                    {member.avatar}
                  </div>
                  <h3 className="font-display font-700 text-ink text-lg leading-tight">{member.name}</h3>
                  <div className="flex items-center gap-2">
                    {[
                      { icon: <Github className="w-4 h-4" />,   href: member.github,   label: 'GitHub' },
                      { icon: <Linkedin className="w-4 h-4" />, href: member.linkedin, label: 'LinkedIn' },
                      { icon: <Mail className="w-4 h-4" />,     href: member.email,    label: 'Email' },
                    ].map((link) => (
                      <a key={link.label} href={link.href} aria-label={link.label}
                        className="w-8 h-8 glass rounded-lg flex items-center justify-center text-ink/40 hover:text-primary-500 transition-colors">
                        {link.icon}
                      </a>
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Institution */}
        <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mt-14 glass-strong p-8 rounded-2xl text-center">
          <div className="text-5xl mb-4">🏫</div>
          <h3 className="font-display font-700 text-ink text-xl mb-2">[University / Institution Name]</h3>
          <p className="text-ink/40 text-sm">[Department] · [College] · [City, Country]</p>
          <p className="text-ink/30 text-xs mt-2 font-mono">Academic Year [20XX – 20XX]</p>
        </motion.div>
      </div>
    </div>
  )
}
