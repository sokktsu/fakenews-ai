'use client'
import { motion } from 'framer-motion'
import { Target, BookOpen, Lightbulb, BarChart3, Shield, Brain } from 'lucide-react'

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
            <BookOpen className="w-3 h-3" /> Thesis Documentation
          </motion.div>
          <motion.h1 variants={fadeUp} className="text-4xl sm:text-5xl font-display font-800 text-ink mb-4">
            About This <span className="text-gradient">Research</span>
          </motion.h1>
          <motion.p variants={fadeUp} className="text-ink/50 text-lg max-w-2xl mx-auto">
            A comprehensive study on leveraging Artificial Intelligence to detect and combat fake news in the digital age.
          </motion.p>
        </motion.div>

        {/* Thesis Background */}
        <motion.section initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass-strong p-8 mb-8">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-2xl font-display font-700 text-ink">Background</h2>
          </div>
          <div className="space-y-4 text-ink/60 leading-relaxed">
            <p>
              The proliferation of fake news has become one of the most pressing challenges of the digital era. 
              Social media platforms and online news aggregators have amplified misinformation at an unprecedented scale, 
              influencing public opinion, political discourse, and even public health decisions.
            </p>
            <p>
              This thesis presents an AI-driven solution that combines Natural Language Processing (NLP) and Deep Learning 
              to automatically detect fake news with high accuracy. By leveraging state-of-the-art transformer models 
              alongside traditional machine learning approaches, we achieve a robust ensemble system.
            </p>
            <p>
              The system was developed in the context of the Philippine information landscape, where misinformation 
              poses unique societal challenges, particularly during election seasons and public health crises.
            </p>
          </div>
        </motion.section>

        {/* Objectives */}
        <motion.section initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass-strong p-8 mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-cyan to-teal-600 flex items-center justify-center">
              <Target className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-2xl font-display font-700 text-ink">Objectives</h2>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            {[
              'Develop an ensemble AI model combining BERT, LSTM, and Logistic Regression for fake news classification',
              'Achieve at least 90% classification accuracy on benchmark fake news datasets',
              'Build an explainable AI system that highlights suspicious content and reasoning',
              'Create an accessible web platform for real-time fake news detection',
              'Implement OCR-based image analysis to detect misinformation in visual media',
              'Establish a self-learning feedback mechanism to continuously improve model performance',
            ].map((obj, i) => (
              <div key={i} className="flex items-start gap-3 glass p-4 rounded-xl">
                <span className="w-6 h-6 rounded-full bg-primary-500/20 text-primary-600 dark:text-primary-400 text-xs font-mono flex items-center justify-center flex-shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <p className="text-ink/60 text-sm leading-relaxed">{obj}</p>
              </div>
            ))}
          </div>
        </motion.section>

        {/* Significance */}
        <motion.section initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass-strong p-8 mb-8">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-magenta to-rose-700 flex items-center justify-center">
              <Lightbulb className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-2xl font-display font-700 text-ink">Significance of the Study</h2>
          </div>
          <div className="grid sm:grid-cols-3 gap-4">
            {[
              { title: 'To Society', desc: 'Empowers citizens to critically evaluate news content and make informed decisions based on verified information.' },
              { title: 'To Journalism', desc: 'Supports fact-checkers and journalists with AI-assisted verification tools, reducing manual verification workload.' },
              { title: 'To AI Research', desc: 'Contributes a novel ensemble approach combining multiple deep learning architectures with explainable AI.' },
            ].map((item) => (
              <div key={item.title} className="glass p-5 rounded-xl">
                <h3 className="font-display font-600 text-primary-600 dark:text-primary-300 mb-2">{item.title}</h3>
                <p className="text-ink/50 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </motion.section>

        {/* Methodology */}
        <motion.section initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass-strong p-8 mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-2xl font-display font-700 text-ink">Methodology</h2>
          </div>
          <div className="space-y-4">
            {[
              { phase: 'Phase 1: Data Collection', desc: 'Collected fake and real news articles from LIAR dataset, FakeNewsNet, and WELFake dataset totaling 70,000+ labeled samples.' },
              { phase: 'Phase 2: Preprocessing', desc: 'Text cleaning, tokenization, stopword removal, lemmatization using NLTK and SpaCy. Applied data augmentation for class balancing.' },
              { phase: 'Phase 3: Model Training', desc: 'Fine-tuned BERT-base-uncased on the dataset. Trained BiLSTM with GloVe embeddings. Fitted TF-IDF + Logistic Regression baseline.' },
              { phase: 'Phase 4: Ensemble', desc: 'Combined predictions using weighted voting: BERT(60%) + LSTM(25%) + LogReg(15%), calibrated using validation set performance.' },
              { phase: 'Phase 5: Explainability', desc: 'Integrated SHAP values, BERT attention visualization, and keyword highlighting for human-interpretable explanations.' },
              { phase: 'Phase 6: Evaluation', desc: 'Evaluated on held-out test sets using Accuracy, Precision, Recall, F1-Score, and ROC-AUC metrics.' },
            ].map((step, i) => (
              <div key={i} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-8 h-8 rounded-full bg-primary-500/20 text-primary-600 dark:text-primary-400 text-sm font-mono font-600 flex items-center justify-center flex-shrink-0">
                    {i + 1}
                  </div>
                  {i < 5 && <div className="w-px flex-1 bg-ink/10 my-2" />}
                </div>
                <div className="pb-4">
                  <h4 className="font-display font-600 text-ink mb-1">{step.phase}</h4>
                  <p className="text-ink/50 text-sm leading-relaxed">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.section>
      </div>
    </div>
  )
}
