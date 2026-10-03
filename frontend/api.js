/**
 * API client for the House Price Prediction backend.
 */

const API_BASE_URL = import.meta.env?.VITE_API_URL || 'http://localhost:8000';

/**
 * Check backend health status.
 * @returns {Promise<{ status: string, model_loaded: boolean }>}
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }
  return response.json();
}

/**
 * Fetch supported categories and location slugs.
 * @returns {Promise<Record<string, string[]>>}
 */
export async function fetchCategories() {
  const response = await fetch(`${API_BASE_URL}/categories`);
  if (!response.ok) {
    throw new Error(`Failed to load categories: ${response.status}`);
  }
  return response.json();
}

/**
 * Send property features to get a price prediction.
 * @param {Object} payload Prediction request payload
 * @returns {Promise<{ predicted_price: number, formatted_price: string }>}
 */
export async function predictPrice(payload) {
  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Prediction failed' }));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }

  return response.json();
}
