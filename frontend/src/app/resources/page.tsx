'use client'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { BookOpen, ExternalLink, Filter, Search } from 'lucide-react'
import { getResources } from '@/lib/api'

const fadeUp = {
  hidden:  { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
}

const CATEGORY_LABELS: Record<string, string> = {
  'fact-checking': '✅ Fact-Checking',
  'tool':          '🛠 Tools',
  'education':     '📚 Education',
  'ai-ethics':     '🤖 AI Ethics',
  'journalism':    '📰 Journalism',
  'research':      '🔬 Research',
}

const CATEGORY_COLORS: Record<string, string> = {
  'fact-checking': 'from-green-500 to-teal-600',
  'tool':          'from-primary-500 to-primary-700',
  'education':     'from-amber-500 to-orange-600',
  'ai-ethics':     'from-purple-500 to-violet-700',
  'journalism':    'from-blue-500 to-cyan-600',
  'research':      'from-rose-500 to-accent-magenta',
}

export default function ResourcesPage() {
  const [resources, setResources] = useState<any[]>([])
  const [filtered,  setFiltered]  = useState<any[]>([])
  const [category,  setCategory]  = useState('all')
  const [search,    setSearch]    = useState('')
  const [loading,   setLoading]   = useState(true)

  useEffect(() => {
    getResources()
      .then((data) => { setResources(data); setFiltered(data) })
      .catch(() => setResources([]))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    let items = resources
    if (category !== 'all') items = items.filter((r) => r.category === category)
    if (search.trim()) {
      const q = search.toLowerCase()
      items = items.filter((r) =>
        r.title.toLowerCase().includes(q) || r.description.toLowerCase().includes(q)
      )
    }
    setFiltered(items)
  }, [category, search, resources])

  const categories = ['all', ...Array.from(new Set(resources.map((r) => r.category)))]

  return (
    <div className="min-h-screen pt-24 pb-20 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} className="text-center mb-12">
          <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-xs font-mono text-primary-600 dark:text-primary-300 mb-6">
            <BookOpen className="w-3 h-3" /> Curated Knowledge Base
          </div>
          <h1 className="text-4xl sm:text-5xl font-display font-800 text-ink mb-4">
            Resources & <span className="text-gradient">Education</span>
          </h1>
          <p className="text-ink/50 text-lg max-w-xl mx-auto">
            Tools, guides, and research to help you navigate the misinformation landscape.
          </p>
        </motion.div>

        {/* Search + Filter */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-strong p-4 rounded-2xl mb-8 flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink/30" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search resources…"
              className="w-full bg-field border border-ink/10 rounded-xl pl-9 pr-4 py-2.5 text-ink placeholder-ink/40 text-sm focus:outline-none focus:border-primary-500/50 transition-all"
            />
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <Filter className="w-4 h-4 text-ink/30 flex-shrink-0" />
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-display font-500 transition-all ${
                  category === cat
                    ? 'bg-primary-500 text-white'
                    : 'glass text-ink/50 hover:text-ink/80'
                }`}
              >
                {cat === 'all' ? 'All' : CATEGORY_LABELS[cat] || cat}
              </button>
            ))}
          </div>
        </motion.div>

        {/* Grid */}
        {loading ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="glass rounded-xl p-6 animate-pulse">
                <div className="h-4 bg-ink/10 rounded mb-3 w-3/4" />
                <div className="h-3 bg-ink/5 rounded mb-2" />
                <div className="h-3 bg-ink/5 rounded w-2/3" />
              </div>
            ))}
          </div>
        ) : (
          <motion.div
            className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4"
            initial="hidden"
            animate="visible"
            variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
          >
            {filtered.map((resource) => (
              <motion.a
                key={resource.id}
                href={resource.url}
                target="_blank"
                rel="noopener noreferrer"
                variants={fadeUp}
                className="glass card-hover p-6 rounded-xl group flex flex-col"
              >
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${CATEGORY_COLORS[resource.category] || 'from-primary-500 to-primary-700'} flex items-center justify-center mb-4 text-white text-lg`}>
                  {CATEGORY_LABELS[resource.category]?.split(' ')[0] || '📄'}
                </div>
                <h3 className="font-display font-600 text-ink mb-2 group-hover:text-primary-500 transition-colors leading-tight">
                  {resource.title}
                </h3>
                <p className="text-ink/50 text-sm leading-relaxed flex-1 mb-4">
                  {resource.description}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-ink/30 font-mono">{resource.source}</span>
                  <ExternalLink className="w-4 h-4 text-ink/30 group-hover:text-primary-500 transition-colors" />
                </div>
              </motion.a>
            ))}
            {filtered.length === 0 && (
              <div className="col-span-full text-center py-16 text-ink/30">
                No resources found for your search.
              </div>
            )}
          </motion.div>
        )}

        {/* Educational callout */}
        <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mt-14 glass-strong p-8 rounded-2xl text-center">
          <h2 className="text-2xl font-display font-700 text-ink mb-3">
            How to Spot Fake News — <span className="text-gradient">Quick Guide</span>
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6 text-left">
            {[
              { step: '1', title: 'Check the Source', desc: 'Verify the website domain and publication history before trusting any article.' },
              { step: '2', title: 'Read Beyond Headlines', desc: 'Sensational headlines are a red flag. Always read the full article for context.' },
              { step: '3', title: 'Check the Date', desc: 'Old stories resurface as new. Ensure the content is current and relevant.' },
              { step: '4', title: 'Cross-Reference', desc: 'If a story is real, other credible outlets will likely report it too.' },
            ].map((item) => (
              <div key={item.step} className="glass p-4 rounded-xl">
                <div className="w-8 h-8 rounded-full bg-primary-500/20 text-primary-600 dark:text-primary-400 font-mono font-700 flex items-center justify-center mb-3">
                  {item.step}
                </div>
                <h4 className="font-display font-600 text-ink text-sm mb-1">{item.title}</h4>
                <p className="text-ink/40 text-xs leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
