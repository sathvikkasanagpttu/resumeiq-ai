import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ResumeIntelligencePage } from '../pages/ResumeIntelligencePage';
import { api } from '../services/api';
import { Resume } from '../types';

vi.mock('../services/api', () => ({
  api: {
    listResumes: vi.fn(),
    getResume: vi.fn(),
    uploadResume: vi.fn(),
    deleteResume: vi.fn(),
  },
}));

const mockResume: Resume = {
  id: 'res-upload-1',
  user_id: 'user-1',
  filename: 'Jane_Doe_Resume.pdf',
  file_type: 'application/pdf',
  file_size: 15420,
  is_active: true,
  created_at: new Date().toISOString(),
  skills_count: 5,
  experience_count: 1,
  raw_text: 'Jane Doe Software Engineer experience with Python and Docker',
  skills: [
    {
      id: 'skill-1',
      resume_id: 'res-upload-1',
      original_text: 'Python 3',
      normalized_skill: 'Python',
      category: 'Backend',
      source_section: 'SKILLS',
      source_evidence: 'Built microservices using Python',
      confidence: 0.95,
      evidence_strength: 'verified',
    },
    {
      id: 'skill-2',
      resume_id: 'res-upload-1',
      original_text: 'Docker',
      normalized_skill: 'Docker',
      category: 'DevOps',
      source_section: 'EXPERIENCE',
      source_evidence: 'Containerized services with Docker',
      confidence: 0.9,
      evidence_strength: 'verified',
    },
  ],
  experiences: [
    {
      id: 'exp-1',
      company: 'TechCorp',
      role: 'Software Engineer',
      is_current: true,
      duration_months: 24,
      bullet_points: ['Built microservices using Python', 'Containerized services with Docker'],
      technologies: ['Python', 'Docker'],
    },
  ],
};

describe('ResumeIntelligencePage Upload Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when no resumes exist', async () => {
    vi.mocked(api.listResumes).mockResolvedValueOnce([]);

    render(
      <ResumeIntelligencePage
        selectedResumeId={null}
        onSelectResume={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('No Resume Uploaded Yet')).toBeInTheDocument();
      expect(screen.getByText(/Upload your resume in PDF, DOCX, or TXT format/i)).toBeInTheDocument();
    });
  });

  it('renders parsed resume details when resume exists', async () => {
    vi.mocked(api.listResumes).mockResolvedValue([mockResume]);
    vi.mocked(api.getResume).mockResolvedValue(mockResume);

    render(
      <ResumeIntelligencePage
        selectedResumeId="res-upload-1"
        onSelectResume={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Jane_Doe_Resume\.pdf/i)).toBeInTheDocument();
      expect(screen.getByText(/TechCorp/i)).toBeInTheDocument();
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    // Check extracted skills
    expect(screen.getAllByText('Python').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Docker').length).toBeGreaterThan(0);
  });

  it('handles file upload successfully', async () => {
    vi.mocked(api.listResumes)
      .mockResolvedValueOnce([]) // initial
      .mockResolvedValueOnce([mockResume]); // after upload
    vi.mocked(api.uploadResume).mockResolvedValueOnce(mockResume);
    vi.mocked(api.getResume).mockResolvedValueOnce(mockResume);

    const onSelectResume = vi.fn();

    const { container } = render(
      <ResumeIntelligencePage
        selectedResumeId={null}
        onSelectResume={onSelectResume}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('No Resume Uploaded Yet')).toBeInTheDocument();
    });

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).not.toBeNull();

    const testFile = new File(['Dummy resume text content'], 'resume.pdf', {
      type: 'application/pdf',
    });

    fireEvent.change(fileInput, { target: { files: [testFile] } });

    await waitFor(() => {
      expect(api.uploadResume).toHaveBeenCalledWith(testFile);
      expect(onSelectResume).toHaveBeenCalledWith('res-upload-1');
    });
  });

  it('displays error banner when file upload fails', async () => {
    vi.mocked(api.listResumes).mockResolvedValueOnce([]);
    vi.mocked(api.uploadResume).mockRejectedValueOnce(
      new Error('File size exceeds the 10 MB limit')
    );

    const { container } = render(
      <ResumeIntelligencePage
        selectedResumeId={null}
        onSelectResume={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('No Resume Uploaded Yet')).toBeInTheDocument();
    });

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const testFile = new File(['Large content'], 'huge.pdf', {
      type: 'application/pdf',
    });

    fireEvent.change(fileInput, { target: { files: [testFile] } });

    await waitFor(() => {
      expect(screen.getByText('File size exceeds the 10 MB limit')).toBeInTheDocument();
    });
  });

  it('handles resume deletion after confirmation', async () => {
    vi.mocked(api.listResumes)
      .mockResolvedValueOnce([mockResume]) // initial
      .mockResolvedValueOnce([]); // after delete
    vi.mocked(api.getResume).mockResolvedValue(mockResume);
    vi.mocked(api.deleteResume).mockResolvedValue({} as any);

    // Mock window.confirm
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <ResumeIntelligencePage
        selectedResumeId="res-upload-1"
        onSelectResume={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Jane_Doe_Resume.pdf')).toBeInTheDocument();
    });

    const deleteButton = screen.getByTitle('Delete Resume');
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(window.confirm).toHaveBeenCalledWith(
        'Are you sure you want to delete this resume?'
      );
      expect(api.deleteResume).toHaveBeenCalledWith('res-upload-1');
    });
  });
});
