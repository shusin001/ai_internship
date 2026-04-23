import api from './client';

export async function analyzeGuidance(userId, jobId) {
  const { data } = await api.post('/guidance/analyze', { user_id: userId, job_id: jobId });
  return data;
}
