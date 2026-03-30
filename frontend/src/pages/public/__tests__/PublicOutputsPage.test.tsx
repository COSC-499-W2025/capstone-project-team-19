import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import PublicOutputsPage from '../PublicOutputsPage'

vi.mock('react-router-dom', () => ({
  useParams: vi.fn(() => ({ username: 'testuser' })),
  useNavigate: vi.fn(() => vi.fn()),
  useLocation: vi.fn(() => ({ pathname: '/public/testuser/resume' })),
  NavLink: ({ to, children }: { to: string; children: React.ReactNode | ((props: { isActive: boolean }) => React.ReactNode) }) => {
    const content = typeof children === 'function' ? children({ isActive: false }) : children
    return <a href={to}>{content}</a>
  },
  Link: ({ to, children }: { to: string; children: React.ReactNode }) => (
    <a href={to}>{children}</a>
  ),
}))

vi.mock('../../../api/public', () => ({
  publicGetActiveResume: vi.fn(),
  publicDownloadResumeDocx: vi.fn(),
  publicDownloadResumePdf: vi.fn(),
  publicGetPortfolioStatus: vi.fn(),
}))

vi.mock('../../../auth/token', () => ({
  tokenStore: { get: vi.fn(() => null) },
}))

vi.mock('../../../auth/user', () => ({
  getUsername: vi.fn(() => null),
}))

import {
  publicGetActiveResume,
  publicDownloadResumeDocx,
  publicDownloadResumePdf,
  publicGetPortfolioStatus,
} from '../../../api/public'

const baseResume = {
  id: 1,
  name: 'My Resume',
  created_at: null,
  rendered_text: null,
  aggregated_skills: {
    languages: ['TypeScript', 'Python'],
    frameworks: ['React'],
    technical_skills: ['Docker'],
    writing_skills: [],
  },
  projects: [
    {
      project_name: 'Alpha Project',
      project_type: 'personal',
      project_mode: 'solo',
      languages: ['TypeScript'],
      frameworks: ['React'],
      summary_text: null,
      skills: [],
      key_role: 'Frontend Developer',
      contribution_bullets: ['Built the UI', 'Wrote tests'],
      start_date: '2024-01-01',
      end_date: '2024-06-01',
    },
  ],
}

describe('PublicOutputsPage', () => {
  beforeEach(() => {
    vi.mocked(publicGetPortfolioStatus).mockResolvedValue({ exists: true, is_public: true })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('loading and error states', () => {
    it('shows loading state initially', async () => {
      vi.mocked(publicGetActiveResume).mockReturnValue(new Promise(() => {}))
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText('Loading...')).toBeInTheDocument()
      })
    })

    it('shows error message when API fails', async () => {
      vi.mocked(publicGetActiveResume).mockRejectedValue(new Error('Server error'))
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText('Server error')).toBeInTheDocument()
      })
    })

    it('shows empty state when no active resume is set', async () => {
      vi.mocked(publicGetActiveResume).mockResolvedValue(null)
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText('No resume has been set for this portfolio.')).toBeInTheDocument()
      })
    })

    it('does not show empty state while loading', () => {
      vi.mocked(publicGetActiveResume).mockReturnValue(new Promise(() => {}))
      render(<PublicOutputsPage />)
      expect(screen.queryByText('No resume has been set for this portfolio.')).not.toBeInTheDocument()
    })
  })

  describe('page structure', () => {
    it('renders Resume page heading', async () => {
      vi.mocked(publicGetActiveResume).mockReturnValue(new Promise(() => {}))
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Resume' })).toBeInTheDocument()
      })
    })

    it('calls publicGetActiveResume with the username from params', async () => {
      vi.mocked(publicGetActiveResume).mockResolvedValue(null)
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(publicGetActiveResume).toHaveBeenCalledWith('testuser')
      })
    })
  })

  describe('resume content', () => {
    beforeEach(() => {
      vi.mocked(publicGetActiveResume).mockResolvedValue(baseResume)
    })

    it('renders the resume name', async () => {
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText('My Resume')).toBeInTheDocument()
      })
    })

    it('renders skills section with label', async () => {
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText('Skills')).toBeInTheDocument()
      })
    })

    it('renders languages in skills section', async () => {
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText(/TypeScript, Python/)).toBeInTheDocument()
      })
    })

    it('renders frameworks in skills section', async () => {
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText(/React/)).toBeInTheDocument()
      })
    })

    it('renders technical skills in skills section', async () => {
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText(/Docker/)).toBeInTheDocument()
      })
    })

    it('does not render writing skills row when empty', async () => {
      render(<PublicOutputsPage />)
      await waitFor(() => screen.getByText('My Resume'))
      expect(screen.queryByText(/Writing:/)).not.toBeInTheDocument()
    })

    it('renders projects section heading', async () => {
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText('Projects')).toBeInTheDocument()
      })
    })

    it('renders project name', async () => {
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText('Alpha Project')).toBeInTheDocument()
      })
    })

    it('renders project role and date range as subtitle', async () => {
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText(/Frontend Developer/)).toBeInTheDocument()
      })
    })

    it('renders contribution bullets', async () => {
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText('Built the UI')).toBeInTheDocument()
        expect(screen.getByText('Wrote tests')).toBeInTheDocument()
      })
    })

    it('renders formatted date range for project', async () => {
      render(<PublicOutputsPage />)
      await waitFor(() => {
        // subtitle combines role + date range
        expect(screen.getByText(/Frontend Developer/)).toBeInTheDocument()
        // formatted date range is present (year is always present)
        expect(screen.getByText(/2024/)).toBeInTheDocument()
      })
    })
  })

  describe('project date formatting', () => {
    it('shows "Present" when project has start date but no end date', async () => {
      vi.mocked(publicGetActiveResume).mockResolvedValue({
        ...baseResume,
        projects: [{
          ...baseResume.projects[0],
          start_date: '2024-01-01',
          end_date: null,
        }],
      })
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText(/Present/)).toBeInTheDocument()
      })
    })

    it('shows no date when both start and end are null', async () => {
      vi.mocked(publicGetActiveResume).mockResolvedValue({
        ...baseResume,
        projects: [{
          ...baseResume.projects[0],
          start_date: null,
          end_date: null,
          key_role: null,
        }],
      })
      render(<PublicOutputsPage />)
      await waitFor(() => screen.getByText('Alpha Project'))
      expect(screen.queryByText(/Jan/)).not.toBeInTheDocument()
    })
  })

  describe('project without contribution bullets', () => {
    it('does not render bullet list when empty', async () => {
      vi.mocked(publicGetActiveResume).mockResolvedValue({
        ...baseResume,
        projects: [{
          ...baseResume.projects[0],
          contribution_bullets: [],
        }],
      })
      render(<PublicOutputsPage />)
      await waitFor(() => screen.getByText('Alpha Project'))
      expect(screen.queryByRole('list')).not.toBeInTheDocument()
    })
  })

  describe('export dropdown', () => {
    it('renders export dropdown', async () => {
      vi.mocked(publicGetActiveResume).mockResolvedValue(baseResume)
      vi.mocked(publicDownloadResumeDocx).mockResolvedValue(undefined)
      vi.mocked(publicDownloadResumePdf).mockResolvedValue(undefined)
      render(<PublicOutputsPage />)
      await waitFor(() => screen.getByText('My Resume'))
      // ExportDropdown renders a button with Export label or icon
      expect(screen.getByRole('button')).toBeInTheDocument()
    })
  })

  describe('multiple projects', () => {
    it('renders all projects', async () => {
      vi.mocked(publicGetActiveResume).mockResolvedValue({
        ...baseResume,
        projects: [
          { ...baseResume.projects[0], project_name: 'Project One', start_date: '2024-06-01', end_date: '2024-12-01' },
          { ...baseResume.projects[0], project_name: 'Project Two', start_date: '2023-01-01', end_date: '2023-06-01' },
        ],
      })
      render(<PublicOutputsPage />)
      await waitFor(() => {
        expect(screen.getByText('Project One')).toBeInTheDocument()
        expect(screen.getByText('Project Two')).toBeInTheDocument()
      })
    })

    it('sorts projects with most recent first', async () => {
      vi.mocked(publicGetActiveResume).mockResolvedValue({
        ...baseResume,
        projects: [
          { ...baseResume.projects[0], project_name: 'Older Project', start_date: '2022-01-01', end_date: '2022-06-01' },
          { ...baseResume.projects[0], project_name: 'Newer Project', start_date: '2024-01-01', end_date: '2024-06-01' },
        ],
      })
      render(<PublicOutputsPage />)
      await waitFor(() => {
        const headings = screen.getAllByRole('heading', { level: 4 })
        expect(headings[0]).toHaveTextContent('Newer Project')
        expect(headings[1]).toHaveTextContent('Older Project')
      })
    })
  })
})
