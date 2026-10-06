export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface CandidateSkill {
  id: string;
  resume_id: string;
  original_text: string;
  normalized_skill: string;
  category: string;
  source_section: string;
  source_evidence: string;
  confidence: number;
  evidence_strength: 'verified' | 'weak' | 'inferred' | 'missing' | 'uncertain';
}

export interface CandidateExperience {
  id: string;
  company: string;
  role: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  is_current: boolean;
  duration_months: number;
  description?: string;
  bullet_points: string[];
  technologies: string[];
}

export interface CandidateProject {
  id: string;
  title: string;
  role?: string;
  description: string;
  technologies: string[];
  outcomes: string[];
  url?: string;
}

export interface EvidenceItem {
  id: string;
  entity_type: string;
  entity_name: string;
  context_snippet: string;
  source_section: string;
  evidence_strength: 'verified' | 'weak' | 'inferred' | 'missing' | 'uncertain';
  confidence_score: number;
  action_verb?: string;
  quantified_impact?: string;
}

export interface Resume {
  id: string;
  user_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  is_active: boolean;
  created_at: string;
  skills_count: number;
  experience_count: number;
  raw_text?: string;
  skills?: CandidateSkill[];
  experiences?: CandidateExperience[];
  projects?: CandidateProject[];
  evidence_items?: EvidenceItem[];
}

export interface JobRequirement {
  id: string;
  requirement_text: string;
  category: 'REQUIRED' | 'PREFERRED' | 'RESPONSIBILITY' | 'QUALIFICATION' | 'EXPERIENCE' | 'DOMAIN' | 'BEHAVIORAL' | 'LOCATION';
  importance_weight: number;
  normalized_entities: string[];
}

export interface JobSkill {
  id: string;
  skill_name: string;
  normalized_skill: string;
  is_required: boolean;
  importance_weight: number;
  context_snippet?: string;
}

export interface Job {
  id: string;
  user_id: string;
  title: string;
  company: string;
  description: string;
  location?: string;
  work_model: string;
  seniority: string;
  experience_years_min: number;
  is_active: boolean;
  created_at: string;
  requirements_count?: number;
  skills_count?: number;
  requirements?: JobRequirement[];
  skills?: JobSkill[];
}

export interface MatchComponent {
  component_name: string;
  weight: number;
  raw_score: number;
  weighted_score: number;
  explanation: string;
}

export interface EvidenceCitation {
  entity: string;
  strength: string;
  quote: string;
  source_section: string;
  explanation: string;
}

export interface MatchExplanation {
  headline: string;
  overall_assessment: string;
  top_strengths: string[];
  critical_concerns: string[];
  citations: EvidenceCitation[];
  recommendation_strategy: string;
}

export interface Match {
  id: string;
  resume_id: string;
  job_id: string;
  compatibility_score: number;
  semantic_score: number;
  lexical_score: number;
  required_skill_coverage: number;
  preferred_skill_coverage: number;
  evidence_strength_score: number;
  experience_alignment_score: number;
  seniority_alignment_score: number;
  domain_alignment_score: number;
  education_alignment_score: number;
  preference_alignment_score: number;
  status: string;
  calculation_weights: Record<string, number>;
  components: MatchComponent[];
  explanation_summary: MatchExplanation;
  created_at: string;
}

export interface SkillGap {
  id?: string;
  skill_name: string;
  job_requirement_id?: string;
  gap_severity: 'critical' | 'moderate' | 'minor' | 'transferable' | 'representation';
  candidate_evidence?: string;
  explanation: string;
  recommendation: string;
  confidence: number;
  transferable_from?: string;
}

export interface SkillGapReport {
  match_id: string;
  total_gaps: number;
  critical_gaps_count: number;
  moderate_gaps_count: number;
  minor_gaps_count: number;
  transferable_skills_count: number;
  representation_gaps_count: number;
  gaps: SkillGap[];
}

export interface BulletModification {
  section: string;
  original_text: string;
  optimized_text: string;
  rationale: string;
  grounded_evidence: string;
  unsupported_elements_removed: string[];
  confidence: number;
}

export interface ResumeOptimization {
  match_id: string;
  resume_id: string;
  job_id: string;
  summary_of_changes: string;
  truthfulness_guarantee: string;
  modifications: BulletModification[];
  representation_improvements: string[];
  formatting_recommendations: string[];
  estimated_compatibility_gain: number;
}

export interface GeneratedMaterial {
  id: string;
  match_id: string;
  doc_type: string;
  title: string;
  content: string;
  verification_status: string;
  confidence_score: number;
  grounded_citations: {
    paragraph_or_claim: string;
    cited_resume_evidence: string;
    evidence_strength: string;
    confidence: number;
  }[];
  unsupported_claims_rejected: string[];
}

export interface RoadmapMilestone {
  step_number: number;
  title: string;
  description: string;
  estimated_weeks: number;
  learning_resources: string[];
  hands_on_project_to_prove: string;
  evidence_to_add_to_resume: string;
}

export interface SkillLearningPath {
  skill_name: string;
  priority_level: string;
  job_market_demand: string;
  effort_estimate_hours: number;
  transferable_base?: string;
  milestones: RoadmapMilestone[];
}

export interface CareerRoadmap {
  match_id?: string;
  target_role: string;
  current_seniority_level: string;
  target_seniority_level: string;
  summary_strategy: string;
  learning_paths: SkillLearningPath[];
  estimated_total_weeks: number;
}

export interface JobRecommendation {
  job_id: string;
  title: string;
  company: string;
  location?: string;
  work_model: string;
  compatibility_score: number;
  why_it_matches: string;
  strong_matches: string[];
  potential_gaps: string[];
  transferable_skills: string[];
  risk_factors: string[];
  recommended_strategy: string;
}

export interface MarketAnalytics {
  total_jobs_analyzed: number;
  top_skills: {
    skill_name: string;
    category: string;
    frequency_count: number;
    percentage: number;
    required_ratio: number;
  }[];
  seniority_distribution: {
    seniority: string;
    count: number;
    percentage: number;
  }[];
  domain_distribution: {
    domain: string;
    count: number;
    percentage: number;
  }[];
  candidate_benchmark?: {
    candidate_skills_in_market: string[];
    missing_market_critical_skills: string[];
    candidate_percentile: number;
    summary: string;
  };
}

// ==========================================
// RESUMEIQ V2 AUTO BUILDER & INTELLIGENCE TYPES
// ==========================================

export type SourceType = 'extracted' | 'user_confirmed' | 'ai_suggested_pending';

export interface EvidenceSource {
  source: SourceType;
  source_span?: string;
  confidence?: number;
  is_verified?: boolean;
}

export interface ProfileLink {
  label: string;
  url: string;
  platform?: string;
}

export interface ProfileBasics {
  name: string;
  email: string;
  phone?: string;
  location?: string;
  summary?: string;
  headline?: string;
  links: ProfileLink[];
  metadata?: EvidenceSource;
}

export interface ProfileBullet {
  text: string;
  original_text?: string;
  source: SourceType;
  evidence_ids?: string[];
  change_reason?: string;
  risk_flag?: string;
}

export interface ProfileExperience {
  id: string;
  company: string;
  role: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  is_current: boolean;
  bullets: ProfileBullet[];
  technologies: string[];
  metadata?: EvidenceSource;
}

export interface ProfileProject {
  id: string;
  name: string;
  role?: string;
  description: string;
  bullets: ProfileBullet[];
  technologies: string[];
  url?: string;
  outcomes: string[];
  metadata?: EvidenceSource;
}

export interface ProfileEducation {
  id: string;
  institution: string;
  degree: string;
  field_of_study?: string;
  start_date?: string;
  end_date?: string;
  gpa?: string;
  highlights: string[];
  metadata?: EvidenceSource;
}

export interface ProfileSkill {
  name: string;
  category: string;
  proficiency_level?: string;
  source: SourceType;
  evidence_ids?: string[];
}

export interface ProfileCertification {
  name: string;
  issuer: string;
  date_obtained?: string;
  credential_id?: string;
  url?: string;
  metadata?: EvidenceSource;
}

export interface ProfileAchievement {
  title: string;
  description: string;
  date?: string;
  metadata?: EvidenceSource;
}

export interface CanonicalProfile {
  basics: ProfileBasics;
  experience: ProfileExperience[];
  projects: ProfileProject[];
  education: ProfileEducation[];
  skills: ProfileSkill[];
  certifications: ProfileCertification[];
  achievements: ProfileAchievement[];
  languages: string[];
  custom_sections: Record<string, any>;
}

export type BuilderMode = 'clean_rebuild' | 'role_targeted' | 'fresher' | 'experienced';
export type BuilderTemplate = 'classic' | 'modern_minimal' | 'compact' | 'fresher';

export interface GenerateResumeRequest {
  resume_id: string;
  mode: BuilderMode;
  target_role?: string;
  job_description_text?: string;
  template_id: BuilderTemplate;
  page_target: 1 | 2;
}

export interface ResumeDiffItem {
  id: string;
  version_id: string;
  field_path: string;
  original_text?: string;
  proposed_text: string;
  status: 'pending' | 'accepted' | 'rejected' | 'edited';
  edited_text?: string;
  source: string;
  evidence_ids: string[];
  change_reason?: string;
  risk_flag?: string;
  created_at?: string;
}

export interface DiffReviewAction {
  diff_id: string;
  action: 'accept' | 'reject' | 'edit';
  edited_text?: string;
}

export interface ResumeVersion {
  id: string;
  resume_id: string;
  parent_version_id?: string;
  version_num: number;
  mode: string;
  template_id: string;
  is_published: boolean;
  ats_loss_score: number;
  change_summary?: string;
  canonical_profile: CanonicalProfile;
  diffs: ResumeDiffItem[];
  rendered_html?: string;
  created_at?: string;
}

// Missing-Info Wizard Types
export interface WizardQuestion {
  id: string;
  category: 'summary' | 'metric' | 'link' | 'skill' | 'timeline_gap' | 'project_detail' | string;
  target_entity_id?: string;
  target_section: string;
  prompt_text: string;
  context_hint: string;
  example_answers: string[];
  has_metric_requested: boolean;
}

export interface WizardAnswer {
  question_id: string;
  answer_text: string;
  confirmed_metric?: string;
  confirmed_technologies?: string[];
}

export interface WizardSessionResponse {
  resume_id: string;
  total_questions: number;
  questions: WizardQuestion[];
  summary_message: string;
}

export interface WizardSubmitResponse {
  resume_id: string;
  facts_added_count: number;
  message: string;
  next_step: string;
}

// Quality & Gap Audit Types
export interface QualityIssue {
  issue_type: string;
  severity: 'critical' | 'warning' | 'suggestion';
  message: string;
  target_section: string;
  line_text?: string;
  suggested_fix?: string;
}

export interface QualityComponentScore {
  name: string;
  score: number;
  weight: number;
  grade: string;
  explanation: string;
  issues: QualityIssue[];
}

export interface TimelineAnomaly {
  anomaly_type: string;
  severity: string;
  company_or_entity: string;
  dates: string;
  description: string;
  remediation_hint: string;
}

export interface TimelineAnalysisResult {
  total_career_months: number;
  total_career_years: number;
  anomalies: TimelineAnomaly[];
  has_critical_inconsistency: boolean;
}

export interface ImpliedSkillSuggestion {
  implied_skill: string;
  trigger_text: string;
  context_section: string;
  rationale: string;
  suggested_question: string;
}

export interface ResumeQualityReport {
  resume_id: string;
  overall_quality_score: number;
  readiness_tier: string;
  components: QualityComponentScore[];
  timeline_analysis: TimelineAnalysisResult;
  representation_gaps: ImpliedSkillSuggestion[];
  top_recommendations: string[];
}

export interface ExternalImportRequest {
  resume_id: string;
  platform: 'linkedin' | 'github';
  raw_text: string;
}

export interface ExternalImportResponse {
  status: string;
  platform: string;
  facts_imported: number;
  message: string;
}

// Application Tracker Types
export type TrackerStage = 'saved' | 'applied' | 'interviewing' | 'offer' | 'rejected';

export interface TrackerItem {
  id: string;
  user_id: string;
  job_title: string;
  company_name: string;
  stage: TrackerStage;
  resume_version_id?: string;
  target_job_id?: string;
  notes?: string;
  outcome?: string;
  created_at?: string;
  updated_at?: string;
}

export interface TrackerItemCreate {
  job_title: string;
  company_name: string;
  resume_version_id?: string;
  target_job_id?: string;
  stage?: TrackerStage;
  notes?: string;
}

export interface TrackerItemUpdate {
  stage?: TrackerStage;
  notes?: string;
  outcome?: string;
}

// Interview Prep STAR Types
export interface InterviewPrepQuestion {
  id: string;
  question: string;
  category: string;
  evidence_id?: string;
  context_evidence: string;
  star_skeleton: {
    situation?: string;
    task?: string;
    action?: string;
    result?: string;
    architecture?: string;
    trade_offs?: string;
    impact?: string;
  };
}

export interface InterviewPrepResponse {
  id: string;
  resume_id: string;
  target_role: string;
  total_questions: number;
  questions: InterviewPrepQuestion[];
}

export interface InterviewPrepGenerateRequest {
  resume_id: string;
  target_role?: string;
}

