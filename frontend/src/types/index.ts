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
