import api from './client';

export async function getResumeRecommendations(userId) {
  const { data } = await api.get(`/resume-service/recommendations/${userId}`);
  return data;
}

export async function refreshResumeRecommendations(userId) {
  const { data } = await api.post(`/resume-service/recommendations/${userId}/refresh`);
  return data;
}

export async function getResumeProfile(userId) {
  const { data } = await api.get(`/resume-service/profile/${userId}`);
  return data;
}
