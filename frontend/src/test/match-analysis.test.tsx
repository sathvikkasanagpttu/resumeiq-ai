import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MatchAnalysisPage } from '../pages/MatchAnalysisPage';
import { api } from '../services/api';
import { Match, Resume, Job } from '../types';

vi.mock('../services/api', () => ({
  api: {
    getMatch: vi.fn(),
    computeMatch: vi.fn(),
    getEvidenceModal: vi.fn(),
  },
}));

const mockResume: Resume = {
  id: 'res-1',
  user_id: 'user-1',
  filename: 'John_Doe_Resume.pdf',
  file_type: 'application/pdf',
  file_size: 1024,
  is_active: true,
  created_at: new Date().toISOString(),
  skills_count: 14,
  experience_count: 3,
};

const mockJob: Job = {
  id: 'job-1',
  user_id: 'user-1',
  title: 'Senior Backend Engineer',
  company: 'CloudScale Inc',
  description: 'FastAPI, PostgreSQL, Redis, Kubernetes required.',
  work_model: 'remote',
  seniority: 'senior',
  experience_years_min: 5,
  is_active: true,
  created_at: new Date().toISOString(),
  requirements_count: 8,
};

const mockMatch: Match = {
  id: 'match-1',
  resume_id: 'res-1',
  job_id: 'job-1',
  compatibility_score: 87.5,
  semantic_score: 85.0,
  lexical_score: 80.0,
  required_skill_coverage: 90.0,
  preferred_skill_coverage: 75.0,
  evidence_strength_score: 88.0,
  experience_alignment_score: 95.0,
  seniority_alignment_score: 90.0,
  domain_alignment_score: 85.0,
  education_alignment_score: 80.0,
  preference_alignment_score: 85.0,
  status: 'completed',
  calculation_weights: {
    required_skills: 0.25,
    semantic_fit: 0.20,
    evidence_strength: 0.15,
    experience_alignment: 0.15,
    preferred_skills: 0.08,
    seniority_alignment: 0.07,
    domain_alignment: 0.05,
    education_alignment: 0.05,
  },
  components: [
    {
      component_name: 'Required Skills',
      weight: 0.25,
      raw_score: 90.0,
      weighted_score: 22.5,
      explanation: 'Matches 9 of 10 required skills',
    },
  ],
  explanation_summary: {
    headline: 'Strong Candidate Alignment',
    overall_assessment: 'Candidate exceeds senior requirements with verified FastAPI and Redis experience.',
    top_strengths: [
      'Strong production experience with FastAPI microservices',
      'Solid distributed systems background with Redis',
    ],
    critical_concerns: [
      'Kubernetes experience is inferred rather than directly verified in bullets',
    ],
    citations: [
      {
        entity: 'FastAPI',
        strength: 'verified',
        quote: 'Architected high-throughput REST APIs using FastAPI and PostgreSQL',
        source_section: 'EXPERIENCE',
        explanation: 'Direct production ownership with metrics',
      },
    ],
    recommendation_strategy: 'Highlight Kubernetes infrastructure tasks during technical interview',
  },
  created_at: new Date().toISOString(),
};

describe('MatchAnalysisPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when no match is selected and no resumes/jobs exist', () => {
    render(
      <MatchAnalysisPage
        selectedMatchId={null}
        resumes={[]}
        jobs={[]}
        onSelectMatch={vi.fn()}
        onNavigateToGaps={vi.fn()}
      />
    );

    expect(screen.getByText('No Match Analysis Selected')).toBeInTheDocument();
    expect(screen.getByText(/Please upload at least one resume/i)).toBeInTheDocument();
  });

  it('loads and renders match details when selectedMatchId is provided', async () => {
    vi.mocked(api.getMatch).mockResolvedValueOnce(mockMatch);

    render(
      <MatchAnalysisPage
        selectedMatchId="match-1"
        resumes={[mockResume]}
        jobs={[mockJob]}
        onSelectMatch={vi.fn()}
        onNavigateToGaps={vi.fn()}
      />
    );

    expect(api.getMatch).toHaveBeenCalledWith('match-1');

    await waitFor(() => {
      expect(screen.getByText('Strong Candidate Alignment')).toBeInTheDocument();
      expect(screen.getByText('87.5')).toBeInTheDocument();
      expect(screen.getByText(/Candidate exceeds senior requirements/i)).toBeInTheDocument();
    });

    // Check component score cards
    expect(screen.getByText('Required Skill Coverage')).toBeInTheDocument();
    expect(screen.getByText('Semantic Fit')).toBeInTheDocument();
    expect(screen.getByText('Evidence Strength')).toBeInTheDocument();

    // Check citations
    expect(screen.getByText(/Supporting Resume Citations Grounding This Decision/i)).toBeInTheDocument();
    expect(screen.getByText('"Architected high-throughput REST APIs using FastAPI and PostgreSQL"')).toBeInTheDocument();
  });

  it('triggers computeMatch when clicking Run Compatibility Audit', async () => {
    vi.mocked(api.computeMatch).mockResolvedValue(mockMatch);
    const mockSelect = vi.fn();

    render(
      <MatchAnalysisPage
        selectedMatchId={null}
        resumes={[mockResume]}
        jobs={[mockJob]}
        onSelectMatch={mockSelect}
        onNavigateToGaps={vi.fn()}
      />
    );

    // Initial mount auto-computes match
    await waitFor(() => {
      expect(api.computeMatch).toHaveBeenCalledWith('res-1', 'job-1', undefined);
      expect(mockSelect).toHaveBeenCalledWith('match-1');
      expect(screen.getByText('Strong Candidate Alignment')).toBeInTheDocument();
    });

    // Re-running manually
    const runButton = screen.getByText('Run Compatibility Audit');
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(api.computeMatch).toHaveBeenCalledTimes(2);
    });
  });

  it('allows toggling custom weight sliders', () => {
    render(
      <MatchAnalysisPage
        selectedMatchId={null}
        resumes={[mockResume]}
        jobs={[mockJob]}
        onSelectMatch={vi.fn()}
        onNavigateToGaps={vi.fn()}
      />
    );

    const customizeButton = screen.getByText('Customize Weights');
    expect(screen.queryByText('Custom Scoring Model Parameters')).not.toBeInTheDocument();

    fireEvent.click(customizeButton);
    expect(screen.getByText('Custom Scoring Model Parameters')).toBeInTheDocument();
    expect(screen.getByText('Total Weight: 100% Normalized')).toBeInTheDocument();
  });
});
