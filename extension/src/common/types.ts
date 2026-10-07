export interface ExtUser {
  id: string;
  email: string;
  name?: string;
}

export interface ExtStoredAuth {
  token: string;
  refresh_token: string;
  user: ExtUser;
  paired_at: string;
  expires_at?: string;
  api_base_url: string;
}

export interface ExtSettings {
  api_base_url: string;
  threshold_strong: number; // default 80
  threshold_good: number;   // default 65
  threshold_partial: number;// default 45
  auto_match_on_open: boolean;
  floating_button_enabled: boolean;
}

export interface CapturedJob {
  title: string;
  company: string;
  location?: string;
  description: string;
  url: string;
  source_platform: string;
  work_model?: string;
  salary_snippet?: string;
  content_hash?: string;
  is_job_posting?: boolean;
}

export interface MatchedSkillItem {
  skill: string;
  importance: "required" | "preferred";
  proof_snippet: string;
  evidence_type: string;
  confidence: number;
}

export interface TransferableSkillItem {
  job_skill: string;
  candidate_skill: string;
  similarity: number;
  reasoning: string;
}

export interface SkillGapsBreakdown {
  critical: string[];
  moderate: string[];
  minor: string[];
  representation: string[];
}

export interface ComponentScoresBreakdown {
  required_skill_coverage: number;
  preferred_skill_coverage: number;
  semantic_similarity: number;
  evidence_strength: number;
  experience_duration: number;
  seniority_alignment: number;
  domain_relevance: number;
  education_fit: number;
}

export type MatchVerdict = "Strong Match" | "Good Match" | "Partial Match" | "Weak Match";

export interface QuickMatchResult {
  match_id: string;
  overall_score: number;
  verdict: MatchVerdict;
  component_scores: ComponentScoresBreakdown;
  matched_skills: MatchedSkillItem[];
  transferable_skills: TransferableSkillItem[];
  skill_gaps: SkillGapsBreakdown;
  why_this_verdict: string[];
  cached?: boolean;
}

export interface ResumeSummary {
  id: string;
  filename: string;
  version: number;
  title: string;
  created_at: string;
  skills_count: number;
  experience_count: number;
}

export interface CompareItem {
  resume_id: string;
  resume_name: string;
  version: number;
  overall_score: number;
  verdict: MatchVerdict;
  key_strengths: string[];
  critical_gaps: string[];
  skill_coverage_pct: number;
}

export interface CompareResponse {
  job_title: string;
  job_company: string;
  resumes: CompareItem[];
}

export type ActionType = "tailor" | "cover_letter" | "recruiter_message";

export interface ActionResponse {
  action_type: ActionType;
  generated_content: string;
  grounded_evidence_count: number;
  notes?: string;
}

export interface TrackerSaveResponse {
  success: boolean;
  tracker_id: string;
  status: string;
  message: string;
}

export interface ExtensionMessage<T = any> {
  type: string;
  payload?: T;
}
