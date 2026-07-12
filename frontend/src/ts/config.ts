/**
 * Global frontend configuration for VOA.
 * Update API_BASE_URL to point at your deployed Django backend.
 */
export const API_BASE_URL = "http://localhost:8000/api";

export const STORAGE_KEYS = {
  ACCESS_TOKEN: "voa_access_token",
  REFRESH_TOKEN: "voa_refresh_token",
  USER: "voa_user",
};
