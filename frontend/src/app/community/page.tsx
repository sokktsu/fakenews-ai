'use client'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageCircle, Heart, Plus, Send, Users, TrendingUp, Shield, X } from 'lucide-react'
import { getCommunityPosts, createPost, likePost, getComments, addComment } from '@/lib/api'
import toast from 'react-hot-toast'

const CATEGORIES = [
  { key: 'all',            label: 'All Posts',         icon: '🌐' },
  { key: 'discussion',     label: 'Discussion',        icon: '💬' },
  { key: 'verified_source',label: 'Verified Sources',  icon: '✅' },
  { key: 'trend',          label: 'Trends',            icon: '📈' },
]

function PostCard({ post, onLike }: { post: any; onLike: (id: number) => void }) {
  const [showComments, setShowComments] = useState(false)
  const [comments, setComments]         = useState<any[]>([])
  const [newComment, setNewComment]     = useState('')
  const [submitting, setSubmitting]     = useState(false)

  const loadComments = async () => {
    if (!showComments) {
      const data = await getComments(post.id)
      setComments(data)
    }
    setShowComments(!showComments)
  }

  const handleComment = async () => {
    if (!newComment.trim()) return
    setSubmitting(true)
    try {
      await addComment(post.id, { content: newComment })
      setComments([...comments, { author_name: 'You', content: newComment, created_at: new Date().toISOString(), likes: 0 }])
      setNewComment('')
      toast.success('Comment added!')
    } catch {
      toast.error('Failed to post comment.')
    } finally {
      setSubmitting(false)
    }
  }

  const categoryColors: Record<string, string> = {
    discussion:      'text-primary-600 dark:text-primary-400 bg-primary-500/10 border-primary-500/20',
    verified_source: 'text-real bg-real/10 border-real/20',
    trend:           'text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/20',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass card-hover p-6 rounded-xl"
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className={`text-xs px-2 py-1 rounded-md border font-mono ${categoryColors[post.category] || categoryColors.discussion}`}>
              {CATEGORIES.find(c => c.key === post.category)?.label || post.category}
            </span>
            <span className="text-xs text-ink/30 font-mono">
              {new Date(post.created_at).toLocaleDateString()}
            </span>
          </div>
          <h3 className="font-display font-600 text-ink text-lg leading-tight">{post.title}</h3>
        </div>
      </div>
      <p className="text-ink/50 text-sm leading-relaxed mb-4">{post.content}</p>
      {post.source_url && (
        <a href={post.source_url} target="_blank" rel="noopener noreferrer"
          className="text-xs text-primary-600 dark:text-primary-400 hover:underline mb-4 block truncate">
          🔗 {post.source_url}
        </a>
      )}
      <div className="flex items-center gap-4 pt-3 border-t border-ink/8">
        <button onClick={() => onLike(post.id)} className="flex items-center gap-1.5 text-sm text-ink/40 hover:text-rose-400 transition-colors">
          <Heart className="w-4 h-4" /> {post.likes}
        </button>
        <button onClick={loadComments} className="flex items-center gap-1.5 text-sm text-ink/40 hover:text-primary-500 transition-colors">
          <MessageCircle className="w-4 h-4" />
          {showComments ? 'Hide' : 'Comments'}
        </button>
      </div>

      <AnimatePresence>
        {showComments && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mt-4 space-y-3">
            {comments.map((c, i) => (
              <div key={i} className="glass p-3 rounded-lg">
                <div className="flex justify-between text-xs text-ink/40 mb-1">
                  <span className="font-mono">{c.author_name}</span>
                  <span>{new Date(c.created_at).toLocaleDateString()}</span>
                </div>
                <p className="text-ink/70 text-sm">{c.content}</p>
              </div>
            ))}
            <div className="flex gap-2 mt-3">
              <input
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleComment()}
                placeholder="Add a comment…"
                className="flex-1 bg-field border border-ink/10 rounded-lg px-3 py-2 text-ink placeholder-ink/40 text-sm focus:outline-none focus:border-primary-500/50"
              />
              <button onClick={handleComment} disabled={submitting} className="btn-primary py-2 px-3 text-sm flex items-center gap-1">
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function NewPostModal({ onClose, onPost }: { onClose: () => void; onPost: () => void }) {
  const [title, setTitle]     = useState('')
  const [content, setContent] = useState('')
  const [category, setCategory] = useState('discussion')
  const [url, setUrl]         = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!title.trim() || !content.trim()) { toast.error('Title and content are required.'); return }
    setLoading(true)
    try {
      await createPost({ title, content, category, source_url: url || undefined })
      toast.success('Post published!')
      onPost()
      onClose()
    } catch {
      toast.error('Failed to publish post.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
        onClick={(e) => e.stopPropagation()}
        className="glass-strong p-6 rounded-2xl w-full max-w-lg"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-display font-700 text-ink text-xl">New Post</h2>
          <button onClick={onClose} className="p-2 glass rounded-lg text-ink/50 hover:text-ink transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-ink/40 font-mono uppercase tracking-wider mb-1.5 block">Category</label>
            <div className="flex gap-2 flex-wrap">
              {CATEGORIES.filter(c => c.key !== 'all').map((cat) => (
                <button key={cat.key} onClick={() => setCategory(cat.key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-display transition-all ${category === cat.key ? 'bg-primary-500 text-white' : 'glass text-ink/50 hover:text-ink/80'}`}>
                  {cat.icon} {cat.label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-xs text-ink/40 font-mono uppercase tracking-wider mb-1.5 block">Title</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Post title…"
              className="w-full bg-field border border-ink/10 rounded-xl px-4 py-2.5 text-ink placeholder-ink/40 text-sm focus:outline-none focus:border-primary-500/50" />
          </div>
          <div>
            <label className="text-xs text-ink/40 font-mono uppercase tracking-wider mb-1.5 block">Content</label>
            <textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="Share your thoughts, verified sources, or trends…" rows={4}
              className="w-full bg-field border border-ink/10 rounded-xl px-4 py-2.5 text-ink placeholder-ink/40 text-sm resize-none focus:outline-none focus:border-primary-500/50" />
          </div>
          <div>
            <label className="text-xs text-ink/40 font-mono uppercase tracking-wider mb-1.5 block">Source URL (optional)</label>
            <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…"
              className="w-full bg-field border border-ink/10 rounded-xl px-4 py-2.5 text-ink placeholder-ink/40 text-sm focus:outline-none focus:border-primary-500/50" />
          </div>
          <button onClick={handleSubmit} disabled={loading} className="w-full btn-primary py-3 flex items-center justify-center gap-2">
            {loading ? <div className="w-4 h-4 border-2 border-ink/30 border-t-white rounded-full animate-spin" /> : <><Send className="w-4 h-4" /> Publish Post</>}
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

export default function CommunityPage() {
  const [posts,      setPosts]      = useState<any[]>([])
  const [loading,    setLoading]    = useState(true)
  const [category,   setCategory]   = useState('all')
  const [showModal,  setShowModal]  = useState(false)
  const [page,       setPage]       = useState(1)

  const loadPosts = async () => {
    setLoading(true)
    try {
      const data = await getCommunityPosts(page, category === 'all' ? undefined : category)
      setPosts(data)
    } catch {
      setPosts([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadPosts() }, [category, page])

  const handleLike = async (id: number) => {
    try {
      const updated = await likePost(id)
      setPosts(posts.map(p => p.id === id ? { ...p, likes: updated.likes } : p))
    } catch { /* ignore */ }
  }

  return (
    <div className="min-h-screen pt-24 pb-20 px-4">
      <AnimatePresence>
        {showModal && <NewPostModal onClose={() => setShowModal(false)} onPost={loadPosts} />}
      </AnimatePresence>

      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between mb-10 flex-wrap gap-4">
          <div>
            <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-xs font-mono text-primary-600 dark:text-primary-300 mb-4">
              <Users className="w-3 h-3" /> Community Forum
            </div>
            <h1 className="text-4xl font-display font-800 text-ink mb-2">
              Community <span className="text-gradient">Discussion</span>
            </h1>
            <p className="text-ink/50">Share verified sources, discuss trends, and fight misinformation together.</p>
          </div>
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2 mt-4">
            <Plus className="w-4 h-4" /> New Post
          </button>
        </motion.div>

        {/* Category filter */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {CATEGORIES.map((cat) => (
            <button key={cat.key} onClick={() => { setCategory(cat.key); setPage(1) }}
              className={`px-4 py-2 rounded-xl text-sm font-display font-500 transition-all ${
                category === cat.key ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30' : 'glass text-ink/50 hover:text-ink/80'
              }`}>
              {cat.icon} {cat.label}
            </button>
          ))}
        </div>

        {/* Posts */}
        {loading ? (
          <div className="space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="glass rounded-xl p-6 animate-pulse">
                <div className="h-3 bg-ink/10 rounded w-1/4 mb-3" />
                <div className="h-5 bg-ink/10 rounded w-3/4 mb-3" />
                <div className="h-3 bg-ink/5 rounded mb-2" />
                <div className="h-3 bg-ink/5 rounded w-2/3" />
              </div>
            ))}
          </div>
        ) : posts.length === 0 ? (
          <div className="glass rounded-xl p-16 text-center">
            <MessageCircle className="w-12 h-12 text-ink/20 mx-auto mb-4" />
            <p className="text-ink/30 font-display">No posts yet. Be the first to start a discussion!</p>
            <button onClick={() => setShowModal(true)} className="btn-primary mt-4 flex items-center gap-2 mx-auto">
              <Plus className="w-4 h-4" /> Create Post
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {posts.map((post) => (
              <PostCard key={post.id} post={post} onLike={handleLike} />
            ))}
          </div>
        )}

        {/* Moderation notice */}
        <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="mt-10 glass p-4 rounded-xl flex items-center gap-3">
          <Shield className="w-5 h-5 text-primary-600 dark:text-primary-400 flex-shrink-0" />
          <p className="text-ink/40 text-xs">
            Posts are subject to moderation. Please be respectful and only share verified information.
            Misinformation and harmful content will be removed.
          </p>
        </motion.div>
      </div>
    </div>
  )
}
