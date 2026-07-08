'use client'
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, ShieldAlert, Brain, CheckCircle, FileText, Link as LinkIcon, Upload } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import { analyzeText, analyzeImage, getExplanation, submitFeedback } from '@/lib/api'

// ── Types ─────────────────────────────────────────────────────────────────────
type InputMode = 'text' | 'url' | 'image'
type PredictionResult = {
  article_id: number
  label: 'REAL' | 'FAKE'
  confidence: number
  ensemble_score: number
  bert_score: number
  roberta_score: number
  bert_multilingual_score: number
  lstm_score: number
  logistic_score: number
  sentiment: string
  suspicious_keywords: string[]
  text_preview?: string
  extracted_text?: string
}

// ── Score bar ─────────────────────────────────────────────────────────────────
function ScoreBar({ label, score, color }: { label: string; score: number; color: string }) {
  const pct = Math.round(score * 100)
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-ink/60 font-mono">{label}</span>
        <span className="text-ink/80 font-mono">{pct}%</span>
      </div>
      <div className="progress-bar">
        <motion.div
          className={`progress-fill bg-gradient-to-r ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
        />
      </div>
    </div>
  )
}

// ── Result card ───────────────────────────────────────────────────────────────
function ResultCard({ result, onExplain }: { result: PredictionResult; onExplain: () => void }) {
  const isFake = result.label === 'FAKE'
  const [feedbackGiven, setFeedbackGiven] = useState(false)

  const handleFeedback = async (accurate: boolean) => {
    try {
      await submitFeedback({ article_id: result.article_id, was_accurate: accurate })
      setFeedbackGiven(true)
      toast.success('Thank you for your feedback!')
    } catch {
      toast.error('Could not save feedback.')
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`glass-strong p-6 relative overflow-hidden text-left ${
        isFake ? 'border-fake/30' : 'border-real/30'
      }`}
    >
      <div className="relative">
        {/* Label */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            {isFake
              ? <ShieldAlert className="w-8 h-8 text-fake" />
              : <Shield className="w-8 h-8 text-real" />
            }
            <div>
              <span className={isFake ? 'badge-fake' : 'badge-real'}>
                {result.label}
              </span>
              <p className="text-ink/50 text-xs mt-1">
                {result.confidence.toFixed(1)}% confidence
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-ink/40 font-mono">SENTIMENT</p>
            <p className={`text-sm font-display font-600 ${
              result.sentiment === 'POSITIVE' ? 'text-real'
              : result.sentiment === 'NEGATIVE' ? 'text-fake'
              : 'text-ink/60'
            }`}>{result.sentiment}</p>
          </div>
        </div>

        {/* Confidence arc + 5 model scores */}
        <div className="flex items-start gap-4 mb-6 p-4 rounded-xl bg-field">
          <div className="relative w-20 h-20 flex-shrink-0">
            <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
              <circle cx="40" cy="40" r="32" fill="none" stroke="var(--col-track)" strokeWidth="6" />
              <motion.circle
                cx="40" cy="40" r="32"
                fill="none"
                stroke={isFake ? 'var(--col-fake)' : 'var(--col-real)'}
                strokeWidth="6"
                strokeLinecap="round"
                strokeDasharray={`${2 * Math.PI * 32}`}
                initial={{ strokeDashoffset: 2 * Math.PI * 32 }}
                animate={{ strokeDashoffset: 2 * Math.PI * 32 * (1 - result.confidence / 100) }}
                transition={{ duration: 1.5, ease: 'easeOut' }}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="font-display font-700 text-lg" style={{ color: isFake ? 'var(--col-fake)' : 'var(--col-real)' }}>
                {result.confidence.toFixed(0)}%
              </span>
            </div>
          </div>
          <div className="flex-1 space-y-2">
            <ScoreBar label="BERT (30%)"         score={result.bert_score}              color={isFake ? 'from-rose-500 to-accent-magenta' : 'from-teal-500 to-accent-cyan'} />
            <ScoreBar label="RoBERTa (25%)"      score={result.roberta_score}           color="from-primary-500 to-primary-700" />
            <ScoreBar label="mBERT (20%)"        score={result.bert_multilingual_score} color="from-violet-500 to-purple-700" />
            <ScoreBar label="LSTM (15%)"         score={result.lstm_score}              color="from-teal-500 to-cyan-600" />
            <ScoreBar label="LogReg (10%)"       score={result.logistic_score}          color="from-amber-500 to-orange-600" />
          </div>
        </div>

        {/* Keywords */}
        {result.suspicious_keywords.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-ink/40 font-mono uppercase tracking-wider mb-2">
              Suspicious Keywords
            </p>
            <div className="flex flex-wrap gap-2">
              {result.suspicious_keywords.slice(0, 8).map((kw) => (
                <span key={kw} className="px-2 py-1 text-xs rounded-md bg-fake/10 text-fake border border-fake/20 font-mono">
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-3 mt-5">
          <button
            onClick={onExplain}
            className="flex items-center gap-2 btn-primary text-sm py-2 px-4"
          >
            <Brain className="w-4 h-4" />
            Why is this {result.label.toLowerCase()}?
          </button>
          {!feedbackGiven ? (
            <div className="flex items-center gap-2">
              <p className="text-xs text-ink/40">Accurate?</p>
              <button onClick={() => handleFeedback(true)} className="px-3 py-2 text-xs glass rounded-lg text-real hover:bg-real/10 transition-colors">
                ✓ Yes
              </button>
              <button onClick={() => handleFeedback(false)} className="px-3 py-2 text-xs glass rounded-lg text-fake hover:bg-fake/10 transition-colors">
                ✗ No
              </button>
            </div>
          ) : (
            <span className="text-xs text-ink/40 flex items-center gap-1">
              <CheckCircle className="w-3 h-3 text-real" /> Feedback saved
            </span>
          )}
        </div>
      </div>
    </motion.div>
  )
}

// ── Explanation panel ─────────────────────────────────────────────────────────
function ExplanationPanel({ articleId }: { articleId: number }) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    if (data) return
    setLoading(true)
    try {
      const result = await getExplanation(articleId)
      setData(result)
    } catch {
      setError('Could not load explanation.')
    } finally {
      setLoading(false)
    }
  }

  if (!data && !loading) {
    return (
      <button onClick={load} className="w-full glass rounded-xl p-4 text-ink/50 hover:text-ink/80 text-sm transition-colors flex items-center justify-center gap-2">
        <Brain className="w-4 h-4" /> Load full explanation
      </button>
    )
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass rounded-xl p-5 space-y-4 text-left">
      <h3 className="font-display font-600 text-ink flex items-center gap-2">
        <Brain className="w-5 h-5 text-primary-600 dark:text-primary-400" /> AI Explanation
      </h3>
      {loading && (
        <div className="flex items-center gap-2 text-ink/50 text-sm">
          <div className="w-4 h-4 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
          Analyzing reasoning...
        </div>
      )}
      {error && <p className="text-fake text-sm">{error}</p>}
      {data && (
        <div className="space-y-3">
          {data.full_explanation && (
            <p className="text-ink/70 text-sm leading-relaxed whitespace-pre-line">{data.full_explanation}</p>
          )}
          {data.highlighted_sentences?.length > 0 && (
            <div>
              <p className="text-xs text-ink/40 font-mono uppercase tracking-wider mb-2">Suspicious Passages</p>
              {data.highlighted_sentences.map((s: string, i: number) => (
                <p key={i} className="text-sm text-amber-700 dark:text-amber-300 bg-amber-500/10 border-l-2 border-amber-400/40 pl-3 py-1 mb-1 rounded-r">{s}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </motion.div>
  )
}

// ── Image dropzone ────────────────────────────────────────────────────────────
function ImageDropzone({ onResult }: { onResult: (r: PredictionResult) => void }) {
  const [loading, setLoading] = useState(false)
  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.gif'] },
    maxFiles: 1,
    onDrop: async (files) => {
      if (!files[0]) return
      setLoading(true)
      try {
        const result = await analyzeImage(files[0])
        onResult(result)
        toast.success('Image analyzed!')
      } catch {
        toast.error('Image analysis failed.')
      } finally {
        setLoading(false)
      }
    },
  })

  return (
    <div
      {...getRootProps()}
      className={`relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
        isDragActive
          ? 'border-primary-500 bg-primary-500/5'
          : 'border-ink/20 hover:border-primary-500/50 hover:bg-ink/[0.03]'
      }`}
    >
      <input {...getInputProps()} />
      {loading ? (
        <div className="flex flex-col items-center gap-3">
          <div className="w-9 h-9 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
          <p className="text-ink/60 text-sm">Extracting text with OCR…</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2">
          <div className="w-11 h-11 rounded-xl bg-field flex items-center justify-center">
            <Upload className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          </div>
          <p className="text-ink/70 font-display font-500 text-sm">
            {acceptedFiles[0] ? acceptedFiles[0].name : 'Drop image here or click to upload'}
          </p>
          <p className="text-ink/40 text-xs">JPG, PNG, WebP up to 10MB • OCR text extraction</p>
        </div>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function HomePage() {
  const [mode, setMode] = useState<InputMode>('text')
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<PredictionResult | null>(null)
  const [showExplanation, setShowExplanation] = useState(false)
  const resultRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-grow the textarea with content, capped by max-h (then it scrolls).
  useEffect(() => {
    const el = inputRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [input, mode])

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) {
      toast.error(mode === 'url' ? 'Please enter a URL first.' : 'Please enter some text first.')
      return
    }
    setLoading(true)
    setResult(null)
    setShowExplanation(false)
    try {
      const res = await analyzeText(mode === 'url' ? { url: input } : { text: input })
      setResult(res)
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
      toast.success(`Analysis complete: ${res.label}`)
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Analysis failed.')
    } finally {
      setLoading(false)
    }
  }

  const handleImageResult = (r: PredictionResult) => {
    setResult(r)
    setShowExplanation(false)
    setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
  }

  const MODES = [
    { key: 'text'  as const, label: 'Text',  icon: <FileText className="w-4 h-4" /> },
    { key: 'url'   as const, label: 'URL',   icon: <LinkIcon className="w-4 h-4" /> },
    { key: 'image' as const, label: 'Image', icon: <Upload className="w-4 h-4" /> },
  ]

  return (
    <div className="min-h-screen flex flex-col">
      <section className="flex-1 flex items-center px-4 pt-14">
        <div className="max-w-3xl w-full mx-auto text-center py-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          >
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-display font-800 text-ink mb-5">
              Fake News Detector
            </h1>
            <p className="text-xl sm:text-2xl text-ink/60 mb-10">
              Verify if the news is <span className="text-real font-semibold">Real</span> or{' '}
              <span className="text-fake font-semibold">Fake</span>
            </p>

            <div className="max-w-xl mx-auto">
              {/* Mode tabs */}
              <div className="flex justify-center gap-1 p-1 bg-field rounded-lg mb-4 w-fit mx-auto">
                {MODES.map((m) => (
                  <button
                    key={m.key}
                    onClick={() => { setMode(m.key); setInput(''); setResult(null) }}
                    className={`flex items-center gap-1.5 py-1.5 px-4 rounded-md text-sm font-display font-500 transition-colors ${
                      mode === m.key
                        ? 'bg-primary-500 text-white'
                        : 'text-ink/60 hover:text-ink'
                    }`}
                  >
                    {m.icon}
                    {m.label}
                  </button>
                ))}
              </div>

              <motion.div key={mode} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.2 }}>
                {mode === 'image' ? (
                  <ImageDropzone onResult={handleImageResult} />
                ) : (
                  <form onSubmit={handleAnalyze} className="flex flex-col items-center gap-3">
                    {mode === 'text' ? (
                      <textarea
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleAnalyze(e)
                        }}
                        placeholder="Input Text Here"
                        rows={2}
                        className="w-full min-h-[52px] max-h-52 overflow-y-auto resize-none bg-field border border-ink/15 rounded-lg px-4 py-2.5 text-ink placeholder-ink/40 text-sm leading-relaxed focus:outline-none focus:border-primary-500/60 transition-colors"
                      />
                    ) : (
                      <input
                        type="url"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="https://example.com/article…"
                        className="w-full bg-field border border-ink/15 rounded-lg px-4 py-2.5 text-ink placeholder-ink/40 text-sm focus:outline-none focus:border-primary-500/60 transition-colors"
                      />
                    )}
                    <button
                      type="submit"
                      disabled={loading}
                      className="btn-primary text-sm py-2.5 px-8 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? 'Analyzing…' : 'Submit'}
                    </button>
                  </form>
                )}
              </motion.div>
            </div>
          </motion.div>

          {/* Results */}
          <div ref={resultRef}>
            <AnimatePresence>
              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="mt-10 space-y-4"
                >
                  <ResultCard result={result} onExplain={() => setShowExplanation(true)} />
                  {showExplanation && <ExplanationPanel articleId={result.article_id} />}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </section>
    </div>
  )
}
