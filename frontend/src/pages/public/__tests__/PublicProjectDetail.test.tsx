import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PublicProjectDetailPage from '../PublicProjectDetail'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', () => ({
  useParams: vi.fn(() => ({ username: 'johndoe', id: '42' })),
  useNavigate: vi.fn(() => mockNavigate),
  useLocation: vi.fn(() => ({ pathname: '/public/johndoe/projects/42' })),
  NavLink: ({ to, children }: { to: string; children: React.ReactNode | ((props: { isActive: boolean }) => React.ReactNode) }) => {
    const content = typeof children === 'function' ? children({ isActive: false }) : children
    return <a href={to}>{content}</a>
  },
  Link: ({ to, children }: { to: string; children: React.ReactNode }) => (
    <a href={to}>{children}</a>
  ),
}))

vi.mock('../../../api/public', () => ({
  publicGetProject: vi.fn(),
  publicFetchThumbnailUrl: vi.fn(),
  publicListProjects: vi.fn(),
}))

vi.mock('../../../auth/token', () => ({
  tokenStore: { get: vi.fn(() => null) },
}))

vi.mock('../../../auth/user', () => ({
  getUsername: vi.fn(() => null),
}))

import {
  publicGetProject,
  publicFetchThumbnailUrl,
  publicListProjects,
} from '../../../api/public'

const baseProject = {
  project_summary_id: 42,
  project_name: 'Test Project',
  project_type: 'personal',
  project_mode: 'solo',
  created_at: null,
  start_date: null,
  end_date: null,
  summary_text: 'A test summary.',
  languages: ['TypeScript'],
  frameworks: ['React'],
  skills: ['frontend_dev'],
}

function setupDefaultMocks() {
  vi.mocked(publicGetProject).mockResolvedValue(baseProject)
  vi.mocked(publicFetchThumbnailUrl).mockResolvedValue(null)
  vi.mocked(publicListProjects).mockResolvedValue([
    { project_summary_id: 42, project_name: 'Test Project', project_type: null, project_mode: null, created_at: null },
  ])
}

describe('PublicProjectDetailPage', () => {
  beforeEach(() => {
    vi.stubGlobal('URL', {
      createObjectURL: vi.fn(() => 'blob:mock-url'),
      revokeObjectURL: vi.fn(),
    })
    setupDefaultMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.unstubAllGlobals()
  })

  describe('loading and error states', () => {
    it('shows loading state initially', () => {
      vi.mocked(publicGetProject).mockReturnValue(new Promise(() => {}))
      render(<PublicProjectDetailPage />)
      expect(screen.getByText('Loading…')).toBeInTheDocument()
    })

    it('shows error message when API fails', async () => {
      vi.mocked(publicGetProject).mockRejectedValue(new Error('Not found'))
      render(<PublicProjectDetailPage />)
      await waitFor(() => {
        expect(screen.getByText('Not found')).toBeInTheDocument()
      })
    })

    it('shows back button on error state', async () => {
      vi.mocked(publicGetProject).mockRejectedValue(new Error('Failed'))
      render(<PublicProjectDetailPage />)
      await waitFor(() => {
        expect(screen.getByText('← Back to Projects')).toBeInTheDocument()
      })
    })

    it('navigates back to projects list when back button is clicked in error state', async () => {
      vi.mocked(publicGetProject).mockRejectedValue(new Error('Failed'))
      const user = userEvent.setup()
      render(<PublicProjectDetailPage />)
      await waitFor(() => screen.getByText('← Back to Projects'))
      await user.click(screen.getByText('← Back to Projects'))
      expect(mockNavigate).toHaveBeenCalledWith('/public/johndoe/projects')
    })
  })

  describe('project content', () => {
    it('renders project name after loading', async () => {
      render(<PublicProjectDetailPage />)
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Test Project' })).toBeInTheDocument()
      })
    })

    it('renders project summary text', async () => {
      render(<PublicProjectDetailPage />)
      await waitFor(() => {
        expect(screen.getByText('A test summary.')).toBeInTheDocument()
      })
    })

    it('renders project type and mode metadata', async () => {
      render(<PublicProjectDetailPage />)
      await waitFor(() => {
        expect(screen.getByText('personal')).toBeInTheDocument()
        expect(screen.getByText('solo')).toBeInTheDocument()
      })
    })

    it('shows no-image placeholder when thumbnail is null', async () => {
      render(<PublicProjectDetailPage />)
      await waitFor(() => {
        expect(screen.getByText('No Image')).toBeInTheDocument()
      })
    })

    it('does not show no-image placeholder when thumbnail is present', async () => {
      vi.mocked(publicFetchThumbnailUrl).mockResolvedValue('blob:mock-url')
      render(<PublicProjectDetailPage />)
      await waitFor(() => {
        expect(screen.queryByText('No Image')).not.toBeInTheDocument()
      })
    })

    it('renders breadcrumb link back to projects list', async () => {
      render(<PublicProjectDetailPage />)
      await waitFor(() => {
        const link = screen.getByRole('link', { name: 'Projects' })
        expect(link).toHaveAttribute('href', '/public/johndoe/projects')
      })
    })
  })

  describe('skills and technologies', () => {
    it('renders languages', async () => {
      const user = userEvent.setup()
      render(<PublicProjectDetailPage />)
      await waitFor(() => screen.getByText('Skills & Technologies'))
      await user.click(screen.getByText('Skills & Technologies'))
      await waitFor(() => {
        expect(screen.getByText(/TypeScript/)).toBeInTheDocument()
      })
    })

    it('renders frameworks', async () => {
      const user = userEvent.setup()
      render(<PublicProjectDetailPage />)
      await waitFor(() => screen.getByText('Skills & Technologies'))
      await user.click(screen.getByText('Skills & Technologies'))
      await waitFor(() => {
        expect(screen.getByText(/React/)).toBeInTheDocument()
      })
    })

    it('renders skills with formatted names', async () => {
      const user = userEvent.setup()
      render(<PublicProjectDetailPage />)
      await waitFor(() => screen.getByText('Skills & Technologies'))
      await user.click(screen.getByText('Skills & Technologies'))
      await waitFor(() => {
        expect(screen.getByText(/Frontend Dev/)).toBeInTheDocument()
      })
    })

    it('does not render skills section when all arrays are empty', async () => {
      vi.mocked(publicGetProject).mockResolvedValue({
        ...baseProject,
        languages: [],
        frameworks: [],
        skills: [],
      })
      render(<PublicProjectDetailPage />)
      await waitFor(() => screen.getByRole('heading', { name: 'Test Project' }))
      expect(screen.queryByText('Skills & Technologies')).not.toBeInTheDocument()
    })
  })

  describe('collaborative project', () => {
    it('shows contribution summary section for collaborative projects', async () => {
      vi.mocked(publicGetProject).mockResolvedValue({
        ...baseProject,
        project_mode: 'collaborative',
      })
      render(<PublicProjectDetailPage />)
      await waitFor(() => {
        expect(screen.getByText('Contribution Summary')).toBeInTheDocument()
        expect(screen.getByText('No contribution summary available.')).toBeInTheDocument()
      })
    })

    it('does not show contribution summary for solo projects', async () => {
      render(<PublicProjectDetailPage />)
      await waitFor(() => screen.getByRole('heading', { name: 'Test Project' }))
      expect(screen.queryByText('Contribution Summary')).not.toBeInTheDocument()
    })
  })

  describe('prev/next navigation', () => {
    it('shows next project button when current is not last', async () => {
      vi.mocked(publicListProjects).mockResolvedValue([
        { project_summary_id: 42, project_name: 'Test Project', project_type: null, project_mode: null, created_at: null },
        { project_summary_id: 43, project_name: 'Next Project', project_type: null, project_mode: null, created_at: null },
      ])
      render(<PublicProjectDetailPage />)
      await waitFor(() => {
        expect(screen.getByText(/Next Project/)).toBeInTheDocument()
      })
    })

    it('shows prev project button when current is not first', async () => {
      vi.mocked(publicListProjects).mockResolvedValue([
        { project_summary_id: 41, project_name: 'Prev Project', project_type: null, project_mode: null, created_at: null },
        { project_summary_id: 42, project_name: 'Test Project', project_type: null, project_mode: null, created_at: null },
      ])
      render(<PublicProjectDetailPage />)
      await waitFor(() => {
        expect(screen.getByText(/Prev Project/)).toBeInTheDocument()
      })
    })

    it('navigates to next project when next button is clicked', async () => {
      vi.mocked(publicListProjects).mockResolvedValue([
        { project_summary_id: 42, project_name: 'Test Project', project_type: null, project_mode: null, created_at: null },
        { project_summary_id: 43, project_name: 'Next Project', project_type: null, project_mode: null, created_at: null },
      ])
      const user = userEvent.setup()
      render(<PublicProjectDetailPage />)
      await waitFor(() => screen.getByText(/Next Project/))
      await user.click(screen.getByText(/Next Project/))
      expect(mockNavigate).toHaveBeenCalledWith('/public/johndoe/projects/43')
    })

    it('navigates to prev project when prev button is clicked', async () => {
      vi.mocked(publicListProjects).mockResolvedValue([
        { project_summary_id: 41, project_name: 'Prev Project', project_type: null, project_mode: null, created_at: null },
        { project_summary_id: 42, project_name: 'Test Project', project_type: null, project_mode: null, created_at: null },
      ])
      const user = userEvent.setup()
      render(<PublicProjectDetailPage />)
      await waitFor(() => screen.getByText(/Prev Project/))
      await user.click(screen.getByText(/Prev Project/))
      expect(mockNavigate).toHaveBeenCalledWith('/public/johndoe/projects/41')
    })

    it('hides nav row when project is the only one', async () => {
      render(<PublicProjectDetailPage />)
      await waitFor(() => screen.getByRole('heading', { name: 'Test Project' }))
      expect(screen.queryByText(/← /)).not.toBeInTheDocument()
    })
  })
})
