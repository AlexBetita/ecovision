/**
 * API service module for making requests to the backend
 */

const API_BASE_URL = "/api/v1";

/**
 * Helper to build query string from filters object
 */
const toQuery = (filters = {}) => {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== "") {
      params.append(key, value);
    }
  }
  return params.toString();
};

/**
 * Fetch climate data with optional filters
 * @param {Object} filters - Filter parameters
 * @returns {Promise} - API response
 */
export const getClimateData = async (filters = {}) => {
  try {
    const query = toQuery({
      location_id: filters.locationId,
      start_date: filters.startDate,
      end_date: filters.endDate,
      metric: filters.metric,
      quality_threshold: filters.qualityThreshold,
      page: filters.page || 1,
      per_page: filters.perPage || 50,
    });
    const res = await fetch(`${API_BASE_URL}/climate?${query}`);
    if (!res.ok) throw new Error("Failed to fetch climate data");
    return await res.json();
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
};

/**
 * Fetch all available locations
 * @returns {Promise} - API response
 */
export const getLocations = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/locations`);
    if (!res.ok) throw new Error("Failed to fetch locations");
    return await res.json();
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
};

/**
 * Fetch all available metrics
 * @returns {Promise} - API response
 */
export const getMetrics = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/metrics`);
    if (!res.ok) throw new Error("Failed to fetch metrics");
    return await res.json();
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
};

/**
 * Fetch climate summary statistics with optional filters
 * @param {Object} filters - Filter parameters
 * @returns {Promise} - API response
 */
export const getClimateSummary = async (filters = {}) => {
  try {
    const query = toQuery({
      location_id: filters.locationId,
      start_date: filters.startDate,
      end_date: filters.endDate,
      metric: filters.metric,
      quality_threshold: filters.qualityThreshold,
    });
    const res = await fetch(`${API_BASE_URL}/summary?${query}`);
    if (!res.ok) throw new Error("Failed to fetch summary");
    return await res.json();
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
};


/**
 * Fetch climate trends with optional filters
 * @param {Object} filters - Filter parameters
 * @returns {Promise} - API response
 */
export const getClimateTrends = async (filters = {}) => {
  try {
    const query = toQuery({
      location_id: filters.locationId,
      start_date: filters.startDate,
      end_date: filters.endDate,
      metric: filters.metric,
      quality_threshold: filters.qualityThreshold,
    });
    const res = await fetch(`${API_BASE_URL}/trends?${query}`);
    if (!res.ok) throw new Error("Failed to fetch trends");
    return await res.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};