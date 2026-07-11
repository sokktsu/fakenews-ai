'use client'
import { motion } from 'framer-motion'
import { ScrollText } from 'lucide-react'

const fadeUp = {
  hidden:  { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
}

const SECTIONS = [
  {
    title: '1. Acceptance of Terms',
    body:
      'By accessing or using FakeNewsAI ("the Service"), you agree to be bound by these Terms of Service. If you do not agree with any part of these terms, please do not use the Service.',
  },
  {
    title: '2. Nature of the Service',
    body:
      'FakeNewsAI is an academic thesis project that uses machine-learning models to estimate the likelihood that a news article is misinformation. All verdicts are probabilistic estimates, not statements of fact. The Service is provided for educational and research purposes only and must not be treated as an authoritative fact-checking source, professional advice, or a substitute for your own judgment and verification.',
  },
  {
    title: '3. No Warranty',
    body:
      'The Service is provided "as is" and "as available", without warranties of any kind, express or implied. We do not guarantee that predictions are accurate, that the Service will be uninterrupted or error-free, or that it is fit for any particular purpose. AI models can and do make mistakes — including confidently labeling real news as fake and vice versa.',
  },
  {
    title: '4. Acceptable Use',
    body:
      'You agree to use the Service lawfully and reasonably. You may not: (a) use automated tools to flood the Service with requests beyond its published rate limits; (b) attempt to disrupt, reverse-engineer, or gain unauthorized access to the Service or its infrastructure; (c) use the Service to harass, defame, or harm others, including presenting its outputs as definitive proof that a person or publication is spreading misinformation.',
  },
  {
    title: '5. Submitted Content & Data',
    body:
      'Text, URLs, and images you submit for analysis, along with the resulting predictions and any feedback you provide, may be stored in our database and used to evaluate and improve the models (for example, as part of a human-verified retraining pool). Do not submit personal, sensitive, or confidential information. Community posts and comments you publish are visible to other users.',
  },
  {
    title: '6. Accounts',
    body:
      'If you create an account, you are responsible for keeping your credentials secure and for all activity under your account. We may suspend accounts that violate these terms.',
  },
  {
    title: '7. Intellectual Property',
    body:
      'The Service\'s code, design, and trained models belong to the FakeNewsAI thesis team and are used for academic purposes. Third-party datasets, libraries, and pre-trained models remain the property of their respective owners and are used under their applicable licenses.',
  },
  {
    title: '8. Limitation of Liability',
    body:
      'To the maximum extent permitted by law, the FakeNewsAI team, its members, adviser, and institution shall not be liable for any damages arising from your use of, or inability to use, the Service — including decisions made in reliance on its predictions.',
  },
  {
    title: '9. Changes to the Service and Terms',
    body:
      'As a research project, the Service may change, pause, or shut down at any time without notice. We may update these Terms from time to time; continued use of the Service after changes constitutes acceptance of the updated Terms.',
  },
  {
    title: '10. Contact',
    body:
      'Questions about these Terms or the project can be sent through the Contact page.',
  },
]

export default function TermsPage() {
  return (
    <div className="min-h-screen pt-24 pb-20 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} className="text-center mb-12">
          <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-xs font-mono text-primary-600 dark:text-primary-300 mb-6">
            <ScrollText className="w-3 h-3" /> Legal
          </div>
          <h1 className="text-4xl sm:text-5xl font-display font-800 text-ink mb-4">
            Terms of <span className="text-gradient">Service</span>
          </h1>
          <p className="text-ink/40 text-sm font-mono">Last updated: July 2026</p>
        </motion.div>

        {/* Sections */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{ visible: { transition: { staggerChildren: 0.05 } } }}
          className="space-y-4"
        >
          {SECTIONS.map((section) => (
            <motion.section key={section.title} variants={fadeUp} className="glass p-6 rounded-xl">
              <h2 className="font-display font-700 text-ink mb-2">{section.title}</h2>
              <p className="text-ink/50 text-sm leading-relaxed">{section.body}</p>
            </motion.section>
          ))}
        </motion.div>
      </div>
    </div>
  )
}
