/**
 * utils/api.js
 * Centralized Axios instance for all API calls to the FastAPI backend.
 * Base URL is empty so it uses the same host/port as the frontend (or Vite proxy in dev).
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export default api
