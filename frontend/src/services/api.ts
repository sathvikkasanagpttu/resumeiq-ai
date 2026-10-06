import {
  Resume, Job, Match, SkillGapReport, ResumeOptimization,
  GeneratedMaterial, CareerRoadmap, JobRecommendation, MarketAnalytics
} from '../types';

const BASE_URL = '/api/v1';

let authToken: string | null = localStorage.getItem('resumeiq_token');

export const setAuthToken = (token: string | null) => {
  authToken = token;
  if (token) {
    localStorage.setItem('resumeiq_token', token);
  } else {
    localStorage.removeItem('resumeiq_token');
  }
};

const getHeaders = (isMultipart = false) => {
  const headers: Record<string, string> = {};
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  if (!isMultipart) {
    headers['Content-Type'] = 'application/json';
  }
  return headers;
};

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `Request failed: ${res.statusText}`;
    try {
      const errJson = await res.json();
      errorMsg = errJson.detail || errJson.message || errorMsg;
    } catch (_) {}
    throw new Error(errorMsg);
  }
  return res.json();
}

export const api = {
  // Auth
  async login(email: string, password: string) {
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await handleResponse<{ access_token: string; email: string; full_name: string; role: string }>(res);
    setAuthToken(data.access_token);
    return data;
  },

  async register(email: string, fullName: string, password: string) {
    const res = await fetch(`${BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, full_name: fullName, password, role: 'candidate' })
    });
    const data = await handleResponse<{ access_token: string; email: string; full_name: string }>(res);
    setAuthToken(data.access_token);
    return data;
  },

  async getMe() {
    const res = await fetch(`${BASE_URL}/auth/me`, { headers: getHeaders() });
    return handleResponse(res);
  },

  // Resumes
  async uploadResume(file: File): Promise<Resume> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/resumes/upload`, {
      method: 'POST',
      headers: getHeaders(true),
      body: formData
    });
    return handleResponse<Resume>(res);
  },

  async listResumes(): Promise<Resume[]> {
    const res = await fetch(`${BASE_URL}/resumes`, { headers: getHeaders() });
    return handleResponse<Resume[]>(res);
  },

  async getResume(id: string): Promise<Resume> {
    const res = await fetch(`${BASE_URL}/resumes/${id}`, { headers: getHeaders() });
    return handleResponse<Resume>(res);
  },

  async deleteResume(id: string) {
    const res = await fetch(`${BASE_URL}/resumes/${id}`, {
      method: 'DELETE',
      headers: getHeaders()
    });
    return handleResponse(res);
  },

  // Jobs
  async createJob(payload: { title: string; company: string; description: string; location?: string; work_model?: string }): Promise<Job> {
    const res = await fetch(`${BASE_URL}/jobs`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload)
    });
    return handleResponse<Job>(res);
  },

  async listJobs(): Promise<Job[]> {
    const res = await fetch(`${BASE_URL}/jobs`, { headers: getHeaders() });
    return handleResponse<Job[]>(res);
  },

  async getJob(id: string): Promise<Job> {
    const res = await fetch(`${BASE_URL}/jobs/${id}`, { headers: getHeaders() });
    return handleResponse<Job>(res);
  },

  async deleteJob(id: string) {
    const res = await fetch(`${BASE_URL}/jobs/${id}`, {
      method: 'DELETE',
      headers: getHeaders()
    });
    return handleResponse(res);
  },


  // Matching
  async computeMatch(resumeId: string, jobId: string, weights?: Record<string, number>): Promise<Match> {
    const res = await fetch(`${BASE_URL}/matching`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ resume_id: resumeId, job_id: jobId, weights })
    });
    return handleResponse<Match>(res);
  },

  async getMatch(matchId: string): Promise<Match> {
    const res = await fetch(`${BASE_URL}/matching/${matchId}`, { headers: getHeaders() });
    return handleResponse<Match>(res);
  },

  async getResumeMatches(resumeId: string): Promise<Match[]> {
    const res = await fetch(`${BASE_URL}/matching/resume/${resumeId}`, { headers: getHeaders() });
    return handleResponse<Match[]>(res);
  },

  // Evidence
  async getSkillEvidence(resumeId: string, skillName: string) {
    const res = await fetch(`${BASE_URL}/evidence/${resumeId}/skill/${encodeURIComponent(skillName)}`, {
      headers: getHeaders()
    });
    return handleResponse<any>(res);
  },

  async getEvidenceGraph(resumeId: string) {
    const res = await fetch(`${BASE_URL}/evidence/${resumeId}/graph`, { headers: getHeaders() });
    return handleResponse<{ elements: any[] }>(res);
  },

  async verifyClaim(resumeId: string, claimText: string, targetEntity: string) {
    const res = await fetch(`${BASE_URL}/evidence/${resumeId}/verify-claim?claim_text=${encodeURIComponent(claimText)}&target_entity=${encodeURIComponent(targetEntity)}`, {
      method: 'POST',
      headers: getHeaders()
    });
    return handleResponse<any>(res);
  },

  // Gaps
  async getGapReport(matchId: string): Promise<SkillGapReport> {
    const res = await fetch(`${BASE_URL}/gaps/match/${matchId}`, { headers: getHeaders() });
    return handleResponse<SkillGapReport>(res);
  },

  // Optimization
  async getResumeOptimization(matchId: string): Promise<ResumeOptimization> {
    const res = await fetch(`${BASE_URL}/optimization/match/${matchId}`, { headers: getHeaders() });
    return handleResponse<ResumeOptimization>(res);
  },

  // Applications
  async generateMaterial(matchId: string, docType: string): Promise<GeneratedMaterial> {
    const res = await fetch(`${BASE_URL}/applications/generate`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ match_id: matchId, doc_type: docType })
    });
    return handleResponse<GeneratedMaterial>(res);
  },

  // Career
  async getCareerRoadmap(matchId: string): Promise<CareerRoadmap> {
    const res = await fetch(`${BASE_URL}/career/roadmap/match/${matchId}`, { headers: getHeaders() });
    return handleResponse<CareerRoadmap>(res);
  },

  async getJobRecommendations(resumeId: string): Promise<{ recommendations: JobRecommendation[] }> {
    const res = await fetch(`${BASE_URL}/career/recommendations/resume/${resumeId}`, { headers: getHeaders() });
    return handleResponse<{ recommendations: JobRecommendation[] }>(res);
  },

  // Analytics
  async getMarketAnalytics(resumeId?: string): Promise<MarketAnalytics> {
    const url = resumeId ? `${BASE_URL}/analytics?resume_id=${resumeId}` : `${BASE_URL}/analytics`;
    const res = await fetch(url, { headers: getHeaders() });
    return handleResponse<MarketAnalytics>(res);
  },

  // Health
  async getHealth() {
    const res = await fetch(`${BASE_URL}/health`);
    return handleResponse<{ status: string; database_connected: boolean; ai_engine_ready: boolean }>(res);
  }
};
