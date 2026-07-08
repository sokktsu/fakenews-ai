'use client'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Mail, Send, MapPin, MessageCircle, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ContactPage() {
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' })
  const [loading, setLoading]   = useState(false)
  const [sent,    setSent]      = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name || !form.email || !form.message) { toast.error('Please fill all required fields.'); return }
    setLoading(true)
    // Simulate send — replace with actual email API integration
    await new Promise((r) => setTimeout(r, 1500))
    setSent(true)
    setLoading(false)
    toast.success('Message sent successfully!')
  }

  const fadeUp = { hidden: { opacity: 0, y: 24 }, visible: { opacity: 1, y: 0, transition: { duration: 0.5 } } }

  return (
    <div className="min-h-screen pt-24 pb-20 px-4">
      <div className="max-w-4xl mx-auto">

        <motion.div initial="hidden" animate="visible" variants={fadeUp} className="text-center mb-12">
          <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-xs font-mono text-primary-600 dark:text-primary-300 mb-6">
            <Mail className="w-3 h-3" /> Get in Touch
          </div>
          <h1 className="text-4xl sm:text-5xl font-display font-800 text-ink mb-4">
            Contact <span className="text-gradient">Us</span>
          </h1>
          <p className="text-ink/50 text-lg max-w-xl mx-auto">
            Questions, feedback, or collaboration requests? We'd love to hear from you.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-5 gap-8">
          {/* Contact info */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }} className="lg:col-span-2 space-y-4">
            {[
              { icon: <Mail className="w-5 h-5" />,         label: 'Email',     value: 'fakenewsai@email.com',     color: 'from-primary-500 to-primary-700' },
              { icon: <MapPin className="w-5 h-5" />,       label: 'Location',  value: '[University Name]\n[City, Country]', color: 'from-teal-500 to-accent-cyan' },
              { icon: <MessageCircle className="w-5 h-5" />,label: 'Social',    value: '@FakeNewsAI',               color: 'from-accent-magenta to-rose-600' },
            ].map((item) => (
              <div key={item.label} className="glass p-5 rounded-xl flex items-start gap-4">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${item.color} flex items-center justify-center text-white flex-shrink-0`}>
                  {item.icon}
                </div>
                <div>
                  <p className="text-xs text-ink/40 font-mono uppercase tracking-wider mb-1">{item.label}</p>
                  <p className="text-ink/70 text-sm whitespace-pre-line">{item.value}</p>
                </div>
              </div>
            ))}

            {/* Social links */}
            <div className="glass p-5 rounded-xl">
              <p className="text-xs text-ink/40 font-mono uppercase tracking-wider mb-3">Follow Us</p>
              <div className="flex gap-3">
                {[
                  { label: 'X', href: '#', icon: '𝕏' },
                  { label: 'Instagram', href: '#', icon: '📸' },
                  { label: 'YouTube', href: '#', icon: '▶️' },
                ].map((s) => (
                  <a key={s.label} href={s.href} target="_blank" rel="noopener noreferrer"
                    className="glass rounded-lg px-3 py-2 text-sm flex items-center gap-2 text-ink/50 hover:text-ink hover:border-primary-500/30 transition-all">
                    {s.icon} {s.label}
                  </a>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Form */}
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }} className="lg:col-span-3">
            {sent ? (
              <div className="glass-strong p-10 rounded-2xl text-center">
                <CheckCircle className="w-14 h-14 text-real mx-auto mb-4" />
                <h2 className="font-display font-700 text-ink text-2xl mb-2">Message Sent!</h2>
                <p className="text-ink/50">Thank you for reaching out. We'll get back to you as soon as possible.</p>
                <button onClick={() => setSent(false)} className="btn-primary mt-6 mx-auto">Send Another</button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="glass-strong p-6 sm:p-8 rounded-2xl space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-ink/40 font-mono uppercase tracking-wider mb-1.5 block">Name *</label>
                    <input name="name" value={form.name} onChange={handleChange} placeholder="Your name"
                      className="w-full bg-field border border-ink/10 rounded-xl px-4 py-2.5 text-ink placeholder-ink/40 text-sm focus:outline-none focus:border-primary-500/50 transition-all" />
                  </div>
                  <div>
                    <label className="text-xs text-ink/40 font-mono uppercase tracking-wider mb-1.5 block">Email *</label>
                    <input name="email" type="email" value={form.email} onChange={handleChange} placeholder="your@email.com"
                      className="w-full bg-field border border-ink/10 rounded-xl px-4 py-2.5 text-ink placeholder-ink/40 text-sm focus:outline-none focus:border-primary-500/50 transition-all" />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-ink/40 font-mono uppercase tracking-wider mb-1.5 block">Subject</label>
                  <select name="subject" value={form.subject} onChange={handleChange}
                    className="w-full bg-field border border-ink/10 rounded-xl px-4 py-2.5 text-ink text-sm focus:outline-none focus:border-primary-500/50 transition-all">
                    <option value="" className="bg-dark-200">Select a subject</option>
                    <option value="general" className="bg-dark-200">General Inquiry</option>
                    <option value="thesis" className="bg-dark-200">Thesis Collaboration</option>
                    <option value="technical" className="bg-dark-200">Technical Support</option>
                    <option value="feedback" className="bg-dark-200">Feedback</option>
                    <option value="media" className="bg-dark-200">Media / Press</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-ink/40 font-mono uppercase tracking-wider mb-1.5 block">Message *</label>
                  <textarea name="message" value={form.message} onChange={handleChange} rows={5}
                    placeholder="Write your message here…"
                    className="w-full bg-field border border-ink/10 rounded-xl px-4 py-2.5 text-ink placeholder-ink/40 text-sm resize-none focus:outline-none focus:border-primary-500/50 transition-all" />
                </div>
                <button type="submit" disabled={loading} className="w-full btn-primary py-3 flex items-center justify-center gap-2">
                  {loading
                    ? <><div className="w-4 h-4 border-2 border-ink/30 border-t-white rounded-full animate-spin" /> Sending…</>
                    : <><Send className="w-4 h-4" /> Send Message</>
                  }
                </button>
              </form>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  )
}
