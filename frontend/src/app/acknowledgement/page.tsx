'use client'
import { motion } from 'framer-motion'
import { Heart, Star } from 'lucide-react'

const fadeUp = {
  hidden:  { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
}

export default function AcknowledgementPage() {
  return (
    <div className="min-h-screen pt-24 pb-20 px-4">
      <div className="max-w-3xl mx-auto">

        <motion.div initial="hidden" animate="visible" variants={fadeUp} className="text-center mb-14">
          <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-xs font-mono text-primary-600 dark:text-primary-300 mb-6">
            <Heart className="w-3 h-3 text-rose-400" /> With Gratitude
          </div>
          <h1 className="text-4xl sm:text-5xl font-display font-800 text-ink mb-4">
            Acknowledgements
          </h1>
          <p className="text-ink/50 text-lg">
            This research would not have been possible without the support of many individuals and institutions.
          </p>
        </motion.div>

        {/* Main acknowledgement letter */}
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
          className="glass-strong p-8 sm:p-10 rounded-2xl mb-8 leading-loose text-ink/70 space-y-5">
          <p>
            The completion of this thesis titled <em className="text-ink">"Combating Fake News with AI: Natural Language Processing and Deep Learning"</em> would not have been achievable without the guidance, support, and encouragement of many people to whom we owe our deepest gratitude.
          </p>
          <p>
            First and foremost, we express our sincerest appreciation to our thesis adviser, <strong className="text-ink">[Adviser Name]</strong>, whose expertise, patience, and constructive feedback were instrumental in shaping the direction of this research. Your mentorship has been invaluable throughout this journey.
          </p>
          <p>
            We are grateful to the faculty and staff of the <strong className="text-ink">[Department Name]</strong> at <strong className="text-ink">[University Name]</strong> for providing us with the knowledge, facilities, and environment to pursue this research. Special thanks to the members of our thesis panel, <strong className="text-ink">[Panel Member 1]</strong> and <strong className="text-ink">[Panel Member 2]</strong>, for their insightful critiques and suggestions during the defense.
          </p>
          <p>
            This project made use of open-source tools and datasets made freely available by the global research community, including the HuggingFace Transformers library, TensorFlow, PyTorch, and the LIAR and FakeNewsNet datasets. We are grateful to the researchers who made these resources accessible.
          </p>
          <p>
            We extend our heartfelt thanks to our families and loved ones for their unwavering moral and emotional support. Their encouragement gave us the strength to persevere through the most challenging phases of this research.
          </p>
          <p>
            To our fellow researchers and classmates who provided feedback, suggestions, and healthy debate throughout the process — thank you.
          </p>
          <p>
            Finally, we dedicate this work to everyone striving to build a more informed, truth-seeking digital society. In an era of information overload, critical thinking and technological solutions like this one are more important than ever.
          </p>
          <div className="pt-4 border-t border-ink/10 text-right">
            <p className="text-ink/40 text-sm italic">— The Research Team</p>
            <p className="text-ink/30 text-xs font-mono mt-1">[City], [Year]</p>
          </div>
        </motion.div>

        {/* Recognition cards */}
        <div className="grid sm:grid-cols-2 gap-4">
          {[
            { title: 'Thesis Adviser',        names: '[Adviser Name]',             icon: '🎓', color: 'from-primary-500 to-primary-700' },
            { title: 'Panel Members',         names: '[Member 1] · [Member 2]',    icon: '👥', color: 'from-teal-500 to-accent-cyan' },
            { title: 'Open-Source Community', names: 'HuggingFace · TensorFlow · PyTorch · scikit-learn', icon: '🌐', color: 'from-amber-500 to-orange-600' },
            { title: 'Our Families',          names: 'For endless support and love', icon: '❤️', color: 'from-rose-500 to-accent-magenta' },
          ].map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass p-5 rounded-xl flex gap-4 items-start"
            >
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${item.color} flex items-center justify-center text-2xl flex-shrink-0`}>
                {item.icon}
              </div>
              <div>
                <h3 className="font-display font-600 text-ink mb-1">{item.title}</h3>
                <p className="text-ink/40 text-sm">{item.names}</p>
              </div>
            </motion.div>
          ))}
        </div>

        <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
          className="mt-10 text-center">
          <Star className="w-6 h-6 text-amber-600 dark:text-amber-400 mx-auto mb-2" />
          <p className="text-ink/30 text-sm italic">
            "In the age of information, nothing is more dangerous than the inability to question it."
          </p>
        </motion.div>
      </div>
    </div>
  )
}
