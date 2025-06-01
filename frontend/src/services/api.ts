import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'https://ai-journal-assistant-1.onrender.com';

// Configure axios defaults
axios.defaults.baseURL = API_URL;
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Add request interceptor for logging
axios.interceptors.request.use(
  (config) => {
    console.log('Making request to:', config.url);
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for logging
axios.interceptors.response.use(
  (response) => {
    console.log('Received response from:', response.config.url);
    return response;
  },
  (error) => {
    console.error('Response error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Types
export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface JournalEntry {
  id: number;
  content: string;
  ai_response?: string;
  created_at: string;
  updated_at?: string;
}

export interface Mood {
  id: number;
  mood_score: number;
  mood_label: string;
  notes?: string;
  created_at: string;
}

export interface MoodStats {
  average_mood: number;
  mood_distribution: Record<string, number>;
  mood_trend: Array<{
    date: string;
    average_mood: number;
  }>;
  summary?: string;
}

export interface JournalStats {
  total_entries: number;
  average_entry_length: number;
  most_common_topics: Array<{
    topic: string;
    count: number;
  }>;
  writing_frequency: Record<string, number>;
  word_count_trend: Array<{
    date: string;
    average_word_count: number;
  }>;
}

export interface SentimentAnalysis {
  overall_sentiment: number;
  sentiment_by_topic: Record<string, number>;
  sentiment_trend: Array<{
    date: string;
    average_sentiment: number;
  }>;
}

export interface JournalInsights {
  stats: JournalStats;
  sentiment: SentimentAnalysis;
  top_keywords: string[];
  writing_patterns: Record<string, string>;
  recommendations: string[];
}

export interface DailySummary {
  id: number;
  date: string;
  summary: string;
}

export interface DailyMoodSummary {
  id: number;
  user_id: number;
  date: string;
  average_mood: number;
  mood_distribution: Record<string, number>;
  summary: string;
  created_at: string;
}

// Auth API
export const login = async (username: string, password: string) => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  const response = await axios.post(`${API_URL}/auth/token`, formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });
  return response.data;
};

export const register = async (email: string, username: string, password: string) => {
  const response = await axios.post(`${API_URL}/auth/register`, {
    email,
    username,
    password,
  });
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await axios.get(`${API_URL}/auth/me`);
  return response.data;
};

// Journal API
export const createJournalEntry = async (content: string, aiResponse?: string) => {
  const response = await axios.post(`${API_URL}/journal`, {
    content,
    ai_response: aiResponse,
  });
  return response.data;
};

export const getJournalEntries = async () => {
  const response = await axios.get(`${API_URL}/journal`);
  return response.data;
};

export const updateJournalEntry = async (id: number, content: string, aiResponse?: string) => {
  const response = await axios.put(`${API_URL}/journal/${id}`, {
    content,
    ai_response: aiResponse,
  });
  return response.data;
};

export const deleteJournalEntry = async (id: number) => {
  const response = await axios.delete(`${API_URL}/journal/${id}`);
  return response.data;
};

// AI Response API
export const getAIResponse = async (content: string) => {
  const response = await axios.post(`${API_URL}/journal/ai`, { content });
  return response.data;
};

// Mood API
export const createMood = async (moodScore: number, moodLabel: string, notes?: string) => {
  const response = await axios.post(`${API_URL}/mood`, {
    mood_score: moodScore,
    mood_label: moodLabel,
    notes,
  });
  return response.data;
};

export const getMoods = async () => {
  const response = await axios.get(`${API_URL}/mood`);
  return response.data;
};

export const getMoodStats = async (days: number = 30) => {
  const response = await axios.get(`${API_URL}/mood/stats?days=${days}`);
  return response.data;
};

// Insights API
export const getJournalStats = async (days: number = 30) => {
  const response = await axios.get(`${API_URL}/insights/stats?days=${days}`);
  return response.data;
};

export const getSentimentAnalysis = async (days: number = 30) => {
  const response = await axios.get(`${API_URL}/insights/sentiment?days=${days}`);
  return response.data;
};

export const getJournalInsights = async (days: number = 30) => {
  const response = await axios.get(`${API_URL}/insights/insights?days=${days}`);
  return response.data;
};

// Summary API
export const generateDailySummary = async (date: string | null): Promise<DailySummary> => {
  try {
    console.log("=== generateDailySummary ===");
    console.log("Input date:", date);
    
    // Format date as YYYY-MM-DD if provided
    const formattedDate = date ? date.split('/').reverse().join('-') : null;
    console.log("Formatted date for backend:", formattedDate);
    
    // Send date as a query parameter
    const url = formattedDate ? `/summary/generate?date=${formattedDate}` : '/summary/generate';
    console.log("Request URL:", url);
    
    const response = await axios.post<DailySummary>(url);
    console.log("Response:", response.data);
    console.log("Summary date:", response.data.date);
    console.log("Summary text:", response.data.summary.substring(0, 100) + "...");
    
    return response.data;
  } catch (error) {
    console.error("Error in generateDailySummary:", error);
    throw error;
  }
};

export const getDailySummaries = async () => {
  const response = await axios.get(`${API_URL}/summary`);
  return response.data;
};

export const getDailySummary = async (date: string) => {
  const response = await axios.get(`${API_URL}/summary/${date}`);
  return response.data;
};

export const deleteSummary = async (date: string) => {
  const response = await axios.delete(`${API_URL}/summary/${date}`);
  return response.data;
};

// Mood Functions
export const deleteMood = async (id: number) => {
  const response = await axios.delete(`${API_URL}/mood/${id}`);
  return response.data;
};

// Mood Summary API
export const generateMoodSummary = async (date?: string | null): Promise<DailyMoodSummary> => {
  // Convert date from DD/MM/YYYY to YYYY-MM-DD format
  const formattedDate = date ? date.split('/').reverse().join('-') : null;
  console.log('Sending date to backend:', formattedDate);
  console.log('Request URL:', `${API_URL}/mood/summary/generate`);
  console.log('Request body:', { date: formattedDate });
  const response = await axios.post(`${API_URL}/mood/summary/generate`, { date: formattedDate });
  console.log('Response:', response.data);
  return response.data;
};

export const getMoodSummaries = async () => {
  const response = await axios.get(`${API_URL}/mood/summary`);
  return response.data;
};

export const getMoodSummary = async (date: string) => {
  const response = await axios.get(`${API_URL}/mood/summary/${date}`);
  return response.data;
}; 