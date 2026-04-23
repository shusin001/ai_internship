import api from './client';

export async function getJobById(jobId) {
  const { data } = await api.get(`/jobs/${jobId}`);
  return data;
}

export async function listJobs(params = {}) {
  const { data } = await api.get('/jobs', { params });
  return data;
}
