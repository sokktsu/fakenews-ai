'use client'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Sparkles, ScanSearch, Brain, HeartHandshake, ShieldAlert, Users, ArrowRight } from 'lucide-react'

const fadeUp = {
  hidden:  { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
}

const stagger = {
  visible: { transition: { staggerChildren: 0.12 } },
}

export default function AboutPage() {
  return (
    <div className="min-h-screen pt-24 pb-20 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div variants={stagger} initial="hidden" animate="visible" className="text-center mb-16">
          <motion.div variants={fadeUp} className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-xs font-mono text-primary-600 dark:text-primary-300 mb-6">
            <Sparkles className="w-3 h-3" /> About the Project
          </motion.div>
          <motion.h1 variants={fadeUp} className="text-4xl sm:text-5xl font-display font-800 text-ink mb-4">
            Fighting Fake News <span className="text-gradient">with AI</span>
          </motion.h1>
          <motion.p variants={fadeUp} className="text-ink/50 text-lg max-w-2xl mx-auto">
            A free tool that helps you check whether a news article is likely real or fake — in seconds, powered by artificial intelligence.
          </motion.p>
        </motion.div>

        {/* How It Works */}
        <motion.section initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass-strong p-8 mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
              <ScanSearch className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-2xl font-display font-700 text-ink">How It Works</h2>
          </div>
          <div className="space-y-4">
            {[
              { step: 'Paste or upload', desc: 'Drop in a news article, a link, or even a screenshot of a post — our system can read text straight from images.' },
              { step: 'AI analyzes it', desc: 'Five AI models read the article and each give their own verdict based on how it’s written.' },
              { step: 'Get an explained result', desc: 'You see a REAL or FAKE prediction with a confidence score, plus the exact phrases that raised red flags — so you’re not just trusting a black box.' },
            ].map((item, i) => (
              <div key={i} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-8 h-8 rounded-full bg-primary-500/20 text-primary-600 dark:text-primary-400 text-sm font-mono font-600 flex items-center justify-center flex-shrink-0">
                    {i + 1}
                  </div>
                  {i < 2 && <div className="w-px flex-1 bg-ink/10 my-2" />}
                </div>
                <div className="pb-4">
                  <h4 className="font-display font-600 text-ink mb-1">{item.step}</h4>
                  <p className="text-ink/50 text-sm leading-relaxed">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
          <Link href="/" className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 text-sm font-600 hover:gap-3 transition-all">
            Try the analyzer <ArrowRight className="w-4 h-4" />
          </Link>
        </motion.section>

        {/* What Powers It */}
        <motion.section initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass-strong p-8 mb-8">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-cyan to-teal-600 flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-2xl font-display font-700 text-ink">What Powers It</h2>
          </div>
          <div className="space-y-4 text-ink/60 leading-relaxed">
            <p>
              Behind the scenes, this site runs an <span className="font-600 text-ink">ensemble</span> — five AI models
              working together, like a panel of judges. Three are modern language-understanding models (BERT, RoBERTa,
              and a multilingual model that also handles Filipino text), backed by two classic machine learning models.
              Each judge votes, the votes are weighted, and you get one combined verdict.
            </p>
            <p>
              In testing, the ensemble correctly classified about 98% of articles from standard research datasets.
            </p>
          </div>
          <Link href="/resources" className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 text-sm font-600 mt-5 hover:gap-3 transition-all">
            Curious about the technical details? See our AI Models page <ArrowRight className="w-4 h-4" />
          </Link>
        </motion.section>

        {/* Why We Built It */}
        <motion.section initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass-strong p-8 mb-8">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-magenta to-rose-700 flex items-center justify-center">
              <HeartHandshake className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-2xl font-display font-700 text-ink">Why We Built It</h2>
          </div>
          <div className="space-y-4 text-ink/60 leading-relaxed">
            <p>
              In the Philippines, fake news spreads fastest exactly when the truth matters most — during elections and
              public health crises. Fact-checkers can&apos;t keep up with the volume, and most detection tools aren&apos;t
              built with Filipino readers in mind.
            </p>
            <p>
              We built this platform to give everyone a free, fast first line of defense: a way to pause and check
              before you believe or share.
            </p>
          </div>
        </motion.section>

        {/* Accuracy & Limitations */}
        <motion.section initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass-strong p-8 mb-8">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
              <ShieldAlert className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-2xl font-display font-700 text-ink">Accuracy &amp; Limitations</h2>
          </div>
          <p className="text-ink/60 leading-relaxed mb-5">
            No AI is perfect, and ours is no exception. A few honest notes:
          </p>
          <div className="grid sm:grid-cols-3 gap-4">
            {[
              { title: 'Tested on research data', desc: 'Our accuracy figures come from testing on standard research datasets; real-world articles can be trickier.' },
              { title: 'Style, not facts', desc: 'The AI judges how an article is written, not whether each fact in it is true. A well-written lie can slip through; an oddly-written truth can get flagged.' },
              { title: 'A second opinion', desc: 'Treat the result as a second opinion, not a final verdict. When in doubt, check trusted fact-checkers like VERA Files, Rappler Fact Check, or Tsek.ph.' },
            ].map((item) => (
              <div key={item.title} className="glass p-5 rounded-xl">
                <h3 className="font-display font-600 text-primary-600 dark:text-primary-300 mb-2">{item.title}</h3>
                <p className="text-ink/50 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </motion.section>

        {/* Who We Are */}
        <motion.section initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass-strong p-8 mb-8">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
              <Users className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-2xl font-display font-700 text-ink">Who We Are</h2>
          </div>
          <p className="text-ink/60 leading-relaxed">
            This platform was developed as an undergraduate thesis project by computer science students, driven by a
            shared goal: making the fight against misinformation accessible to every Filipino.
          </p>
          <Link href="/team" className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 text-sm font-600 mt-5 hover:gap-3 transition-all">
            Meet the team <ArrowRight className="w-4 h-4" />
          </Link>
        </motion.section>
      </div>
    </div>
  )
}
