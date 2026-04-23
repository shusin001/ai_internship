import api from './client';

export async function registerUser(formData) {
  const { data } = await api.post('/users/register', formData);
  return data;
}

export async function loginUser(payload) {
  const { data } = await api.post('/users/login', payload);
  return data;
}
