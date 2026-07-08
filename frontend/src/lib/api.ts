import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
})

// ── Text Analysis ─────────────────────────────────────────────────────────────
export async function analyzeText(payload: {
  text?: string
  url?: string
  headline?: string
}) {
  const { data } = await api.post('/analyze-text/', payload)
  return data
}

// ── Image Analysis ────────────────────────────────────────────────────────────
export async function analyzeImage(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/analyze-image/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

// ── Explanation ───────────────────────────────────────────────────────────────
export async function getExplanation(articleId: number) {
  const { data } = await api.get(`/explain-result/${articleId}`)
  return data
}

// ── Feedback ──────────────────────────────────────────────────────────────────
export async function submitFeedback(payload: {
  article_id: number
  was_accurate: boolean
  correct_label?: string
  comment?: string
}) {
  const { data } = await api.post('/feedback/', payload)
  return data
}

// ── Community ─────────────────────────────────────────────────────────────────
export async function getCommunityPosts(page = 1, category?: string) {
  const params: Record<string, any> = { page }
  if (category) params.category = category
  const { data } = await api.get('/community-posts/', { params })
  return data
}

export async function createPost(payload: {
  title: string
  content: string
  category: string
  source_url?: string
}) {
  const { data } = await api.post('/community-posts/', payload)
  return data
}

export async function likePost(postId: number) {
  const { data } = await api.post(`/community-posts/${postId}/like`)
  return data
}

export async function getComments(postId: number) {
  const { data } = await api.get(`/community-posts/${postId}/comments`)
  return data
}

export async function addComment(postId: number, payload: { content: string; author_name?: string }) {
  const { data } = await api.post(`/community-posts/${postId}/comments`, payload)
  return data
}

// ── Resources ─────────────────────────────────────────────────────────────────
export async function getResources(category?: string) {
  const params: Record<string, any> = {}
  if (category) params.category = category
  const { data } = await api.get('/resources/', { params })
  return data
}

// ── Admin Stats ───────────────────────────────────────────────────────────────
export async function getAdminStats() {
  const { data } = await api.get('/admin/stats')
  return data
}

// ── News Feed ─────────────────────────────────────────────────────────────────
export async function getNewsFeed() {
  const { data } = await api.get('/news-feed/')
  return data
}
