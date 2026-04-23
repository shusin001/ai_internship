export function extractApiError(error, fallbackMessage) {
  const detail = error?.response?.data?.detail;

  if (typeof detail === 'string' && detail.trim()) {
    return detail.trim();
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (typeof first === 'string' && first.trim()) {
      return first.trim();
    }
    if (typeof first?.msg === 'string' && first.msg.trim()) {
      const loc = Array.isArray(first.loc) ? first.loc.join(".") : "";
      return loc ? `${loc}: ${first.msg}` : first.msg;
    }
  }

  if (typeof error?.response?.data === 'string' && error.response.data.trim()) {
    return error.response.data.trim();
  }

  if (typeof error?.response?.data?.message === 'string' && error.response.data.message.trim()) {
    return error.response.data.message.trim();
  }

  if (error?.code === 'ERR_NETWORK') {
    return 'Cannot reach backend API. Start FastAPI server on http://127.0.0.1:8000.';
  }

  if (typeof error?.message === 'string' && error.message.trim() && error.message !== 'Network Error') {
    return error.message.trim();
  }

  return fallbackMessage;
}
