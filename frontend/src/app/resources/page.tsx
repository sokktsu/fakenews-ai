'use client'
import { motion } from 'framer-motion'
import { BrainCircuit, Scale } from 'lucide-react'

const fadeUp = {
  hidden:  { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
}

const MODELS = [
  {
    emoji:  '🧠',
    name:   'BERT',
    full:   'Bidirectional Encoder Representations from Transformers',
    weight: '30%',
    color:  'from-primary-500 to-primary-700',
    desc:
      'A transformer model that reads every word in both directions at once, letting it understand each word from its full sentence context. Fine-tuned on our fake/real news dataset, it is the strongest single detector in the ensemble and carries the largest vote.',
    tags: ['Transformer', 'Fine-tuned', '110M parameters'],
  },
  {
    emoji:  '⚡',
    name:   'RoBERTa',
    full:   'Robustly Optimized BERT Approach',
    weight: '25%',
    color:  'from-accent-cyan to-teal-600',
    desc:
      'An improved variant of BERT trained with more data and better training recipes. It shares BERT\'s architecture but often reads nuance more reliably, so it acts as a strong second opinion that catches cases BERT is unsure about.',
    tags: ['Transformer', 'Fine-tuned', '125M parameters'],
  },
  {
    emoji:  '🌏',
    name:   'mBERT',
    full:   'Multilingual BERT',
    weight: '20%',
    color:  'from-violet-500 to-purple-700',
    desc:
      'A version of BERT pre-trained on 104 languages, including Filipino. It handles Tagalog and Taglish (code-switching) articles that the English-only models may misread — essential for analyzing Philippine news content.',
    tags: ['Transformer', 'Multilingual', 'Filipino support'],
  },
  {
    emoji:  '🔁',
    name:   'BiLSTM',
    full:   'Bidirectional Long Short-Term Memory',
    weight: '15%',
    color:  'from-amber-500 to-orange-600',
    desc:
      'A recurrent neural network that reads the article word-by-word, forward and backward, remembering what came before. Lighter than the transformers, it learns writing patterns and word-order cues typical of misinformation.',
    tags: ['Deep learning', 'Sequence model', 'Lightweight'],
  },
  {
    emoji:  '📊',
    name:   'Logistic Regression',
    full:   'Classical machine learning baseline',
    weight: '10%',
    color:  'from-rose-500 to-accent-magenta',
    desc:
      'A classical statistical model working on TF-IDF word frequencies rather than deep context. It is fast, interpretable, and grounds the ensemble — when flashy language fools nobody\'s statistics, it says so.',
    tags: ['Classical ML', 'TF-IDF', 'Interpretable'],
  },
]

const STEPS = [
  { step: '1', title: 'Your article goes in', desc: 'Text is cleaned and tokenized, then sent to all five models at the same time.' },
  { step: '2', title: 'Five independent verdicts', desc: 'Each model outputs its own probability that the article is fake, from 0% to 100%.' },
  { step: '3', title: 'Weighted vote', desc: 'Scores are combined using each model\'s weight (30 / 25 / 20 / 15 / 10) into one ensemble score.' },
  { step: '4', title: 'Final verdict', desc: 'Below 50% → REAL, above 50% → FAKE. The confidence shows how far the score is from the middle.' },
]

export default function ResourcesPage() {
  return (
    <div className="min-h-screen pt-24 pb-20 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} className="text-center mb-12">
          <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-xs font-mono text-primary-600 dark:text-primary-300 mb-6">
            <BrainCircuit className="w-3 h-3" /> Knowledge Base
          </div>
          <h1 className="text-4xl sm:text-5xl font-display font-800 text-ink mb-4">
            Resources & <span className="text-gradient">Education</span>
          </h1>
          <p className="text-ink/50 text-lg max-w-xl mx-auto">
            The AI models powering this detector, and practical guides for navigating misinformation yourself.
          </p>
        </motion.div>

        {/* Section: The AI Models */}
        <div className="flex items-center gap-3 mb-6">
          <BrainCircuit className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          <h2 className="font-display font-700 text-ink text-xl">The AI Models</h2>
        </div>

        {/* Model cards */}
        <motion.div
          className="grid sm:grid-cols-2 gap-4"
          initial="hidden"
          animate="visible"
          variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
        >
          {MODELS.map((model) => (
            <motion.div key={model.name} variants={fadeUp} className="glass card-hover p-6 rounded-xl flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${model.color} flex items-center justify-center text-white text-lg`}>
                  {model.emoji}
                </div>
                <span className="glass px-3 py-1 rounded-full text-xs font-mono text-ink/60">
                  weight {model.weight}
                </span>
              </div>
              <h3 className="font-display font-700 text-ink text-lg leading-tight">{model.name}</h3>
              <p className="text-ink/40 text-xs font-mono mb-3">{model.full}</p>
              <p className="text-ink/50 text-sm leading-relaxed flex-1 mb-4">{model.desc}</p>
              <div className="flex items-center gap-2 flex-wrap">
                {model.tags.map((tag) => (
                  <span key={tag} className="glass px-2 py-0.5 rounded-md text-[10px] font-mono text-ink/40">
                    {tag}
                  </span>
                ))}
              </div>
            </motion.div>
          ))}

          {/* Score meaning card */}
          <motion.div variants={fadeUp} className="glass-strong p-6 rounded-xl flex flex-col justify-center">
            <div className="flex items-center gap-3 mb-3">
              <Scale className="w-5 h-5 text-primary-500" />
              <h3 className="font-display font-700 text-ink text-lg">Reading the scores</h3>
            </div>
            <p className="text-ink/50 text-sm leading-relaxed mb-4">
              Every percentage is that model&apos;s estimate of the probability the article is <b>fake</b>.
            </p>
            <div className="flex items-center justify-between text-xs font-mono mb-1">
              <span className="text-green-500 font-700">0% — REAL</span>
              <span className="text-ink/30">50%</span>
              <span className="text-red-500 font-700">100% — FAKE</span>
            </div>
            <div className="h-2 rounded-full bg-gradient-to-r from-green-500 via-amber-400 to-red-500" />
            <p className="text-ink/40 text-xs leading-relaxed mt-4">
              Models can disagree — that is by design. The weighted ensemble smooths out individual mistakes better than any single model alone.
            </p>
          </motion.div>
        </motion.div>

        {/* How the ensemble works */}
        <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mt-14 glass-strong p-8 rounded-2xl text-center">
          <h2 className="text-2xl font-display font-700 text-ink mb-3">
            How the <span className="text-gradient">Ensemble</span> Works
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6 text-left">
            {STEPS.map((item) => (
              <div key={item.step} className="glass p-4 rounded-xl">
                <div className="w-8 h-8 rounded-full bg-primary-500/20 text-primary-600 dark:text-primary-400 font-mono font-700 flex items-center justify-center mb-3">
                  {item.step}
                </div>
                <h4 className="font-display font-600 text-ink text-sm mb-1">{item.title}</h4>
                <p className="text-ink/40 text-xs leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
          <p className="text-ink/30 text-xs mt-6 font-mono">
            Sentiment (positive / neutral / negative) is analyzed separately as supporting context — it flags emotionally
            manipulative language but does not decide the verdict.
          </p>
        </motion.div>

        {/* Section: How to Spot Fake News */}
        <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mt-14 glass-strong p-8 rounded-2xl text-center">
          <h2 className="text-2xl font-display font-700 text-ink mb-3">
            How to Spot Fake News — <span className="text-gradient">Quick Guide</span>
          </h2>
          <p className="text-ink/40 text-sm max-w-xl mx-auto">
            AI helps, but your own judgment is the best defense. Four habits to verify any story:
          </p>
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
