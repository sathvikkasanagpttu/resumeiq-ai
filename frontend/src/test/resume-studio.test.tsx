import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ResumeStudioPage } from '../pages/ResumeStudioPage';
import { api } from '../services/api';
import { Resume, ResumeVersion, ResumeDiffItem } from '../types';

vi.mock('../services/api', () => ({
  api: {
    listResumeVersions: vi.fn(),
    getResumeVersion: vi.fn(),
    generateResumeVersion: vi.fn(),
    reviewBulletDiff: vi.fn(),
    downloadResumeExport: vi.fn(),
    getMissingInfoSession: vi.fn(),
    submitMissingInfoAnswers: vi.fn(),
    verifyClaims: vi.fn(),
  },
}));

const mockResume: Resume = {
  id: 'res-1',
  user_id: 'user-1',
  filename: 'Alex_Engineer_Resume.pdf',
  file_type: 'application/pdf',
  file_size: 2048,
  is_active: true,
  created_at: new Date().toISOString(),
  skills_count: 10,
  experience_count: 2,
};

const mockDiff: ResumeDiffItem = {
  id: 'diff-1',
  version_id: 'ver-1',
  field_path: 'experience[0].bullets[0]',
  original_text: 'Worked on backend APIs using Python.',
  proposed_text: 'Architected REST APIs using FastAPI and Python, handling 15,000 requests/sec with 99.9% uptime.',
  status: 'pending',
  source: 'extracted',
  evidence_ids: ['ev-1', 'ev-2'],
  change_reason: 'Quantified outcomes and clarified framework from verified evidence',
};

const mockVersion: ResumeVersion = {
  id: 'ver-1',
  resume_id: 'res-1',
  version_num: 1,
  mode: 'clean_rebuild',
  template_id: 'modern_minimal',
  is_published: false,
  ats_loss_score: 96,
  change_summary: 'Synthesized 5 bullet points with outcome metrics; 0 unverified claims.',
  canonical_profile: {
    basics: {
      name: 'Alex Rivera',
      email: 'alex@example.com',
      links: [],
    },
    experience: [
      {
        id: 'exp-1',
        company: 'CloudTech',
        role: 'Senior Software Engineer',
        is_current: true,
        bullets: [
          {
            text: 'Architected REST APIs using FastAPI and Python, handling 15,000 requests/sec with 99.9% uptime.',
            source: 'extracted',
          },
        ],
        technologies: ['FastAPI', 'Python', 'PostgreSQL'],
      },
    ],
    projects: [],
    education: [],
    skills: [
      { name: 'Python', category: 'Backend', source: 'extracted' },
      { name: 'FastAPI', category: 'Backend', source: 'extracted' },
    ],
    certifications: [],
    achievements: [],
    languages: ['English'],
    custom_sections: {},
  },
  diffs: [mockDiff],
  rendered_html: '<div><h1>Alex Rivera</h1></div>',
  created_at: new Date().toISOString(),
};

describe('ResumeStudioPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when no resume is selected', () => {
    render(
      <ResumeStudioPage
        selectedResumeId={null}
        resumes={[]}
        onSelectResume={vi.fn()}
      />
    );

    expect(
      screen.getByText(/Select a resume and click "Build Resume" to preview/i)
    ).toBeInTheDocument();
  });

  it('loads and displays resume versions and diff items', async () => {
    vi.mocked(api.listResumeVersions).mockResolvedValueOnce([mockVersion]);

    render(
      <ResumeStudioPage
        selectedResumeId="res-1"
        resumes={[mockResume]}
        onSelectResume={vi.fn()}
      />
    );

    expect(api.listResumeVersions).toHaveBeenCalledWith('res-1');

    await waitFor(() => {
      expect(screen.getByText('Alex Rivera')).toBeInTheDocument();
      expect(screen.getByText('Version #1')).toBeInTheDocument();
      expect(screen.getByText(/ATS Loss: 96.0%/i)).toBeInTheDocument();
    });

    // Check that diff item is present
    expect(screen.getAllByText(/Architected REST APIs using FastAPI/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Worked on backend APIs using Python/i)).toBeInTheDocument();
  });

  it('handles diff review action (accept diff)', async () => {
    vi.mocked(api.listResumeVersions).mockResolvedValueOnce([mockVersion]);
    const updatedDiff: ResumeDiffItem = { ...mockDiff, status: 'accepted' };
    vi.mocked(api.reviewBulletDiff).mockResolvedValueOnce(updatedDiff);
    vi.mocked(api.getResumeVersion).mockResolvedValueOnce({
      ...mockVersion,
      diffs: [updatedDiff],
    });

    render(
      <ResumeStudioPage
        selectedResumeId="res-1"
        resumes={[mockResume]}
        onSelectResume={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Accept')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Accept'));

    await waitFor(() => {
      expect(api.reviewBulletDiff).toHaveBeenCalledWith({
        diff_id: 'diff-1',
        action: 'accept',
        edited_text: undefined,
      });
    });
  });

  it('triggers new version generation', async () => {
    vi.mocked(api.listResumeVersions).mockResolvedValue([mockVersion]);
    const newVersion: ResumeVersion = {
      ...mockVersion,
      id: 'ver-2',
      version_num: 2,
    };
    vi.mocked(api.generateResumeVersion).mockResolvedValueOnce(newVersion);

    render(
      <ResumeStudioPage
        selectedResumeId="res-1"
        resumes={[mockResume]}
        onSelectResume={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Build Resume')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Build Resume'));

    await waitFor(() => {
      expect(api.generateResumeVersion).toHaveBeenCalledWith(
        expect.objectContaining({
          resume_id: 'res-1',
          mode: 'clean_rebuild',
          template_id: 'modern_minimal',
          page_target: 1,
        })
      );
    });
  });
});
