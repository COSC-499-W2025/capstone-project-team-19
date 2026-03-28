import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import PublicProjectsPage from '../PublicProjects'

vi.mock('react-router-dom', () => ({
  useParams: vi.fn(() => ({ username: 'johndoe' })),
  useNavigate: vi.fn(() => vi.fn()),
  NavLink: ({ to, children }: { to: string; children: React.ReactNode }) => (
    <a href={to}>{children}</a>
  ),
  Link: ({ to, children }: { to: string; children: React.ReactNode }) => (
    <a href={to}>{children}</a>
  ),
}))

vi.mock('../../../api/public', () => ({
  publicListProjects: vi.fn(),
  publicFetchThumbnailUrl: vi.fn(),
  publicGetRanking: vi.fn(),
}))

vi.mock('../../../auth/token', () => ({
  tokenStore: { get: vi.fn(() => null) },
}))

vi.mock('../../../auth/user', () => ({
  getUsername: vi.fn(() => null),
}))

import { publicListProjects, publicFetchThumbnailUrl, publicGetRanking } from '../../../api/public'

describe('PublicProjectsPage', () => {
  beforeEach(() => {
    vi.mocked(publicFetchThumbnailUrl).mockResolvedValue(null)
    vi.mocked(publicGetRanking).mockResolvedValue([])
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially', () => {
    vi.mocked(publicListProjects).mockReturnValue(new Promise(() => {}))
    render(<PublicProjectsPage />)
    expect(screen.getByText('Loading…')).toBeInTheDocument()
  })

  it('renders project cards after successful load', async () => {
    vi.mocked(publicListProjects).mockResolvedValue([
      { project_summary_id: 1, project_name: 'Project Alpha', project_type: null, project_mode: null, created_at: null },
      { project_summary_id: 2, project_name: 'Project Beta', project_type: null, project_mode: null, created_at: null },
    ])
    render(<PublicProjectsPage />)
    await waitFor(() => {
      expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      expect(screen.getByText('Project Beta')).toBeInTheDocument()
    })
  })

  it('shows empty state when no projects exist', async () => {
    vi.mocked(publicListProjects).mockResolvedValue([])
    render(<PublicProjectsPage />)
    await waitFor(() => {
      expect(screen.getByText(/No projects yet/)).toBeInTheDocument()
    })
  })

  it('shows error message when API fails', async () => {
    vi.mocked(publicListProjects).mockRejectedValue(new Error('Network error'))
    render(<PublicProjectsPage />)
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })

  it('does not show empty state while loading', () => {
    vi.mocked(publicListProjects).mockReturnValue(new Promise(() => {}))
    render(<PublicProjectsPage />)
    expect(screen.queryByText(/No projects yet/)).not.toBeInTheDocument()
  })

  it('renders the page heading', () => {
    vi.mocked(publicListProjects).mockReturnValue(new Promise(() => {}))
    render(<PublicProjectsPage />)
    expect(screen.getByRole('heading', { name: 'Projects' })).toBeInTheDocument()
  })

  it('calls publicListProjects with the username from params', async () => {
    vi.mocked(publicListProjects).mockResolvedValue([])
    render(<PublicProjectsPage />)
    await waitFor(() => {
      expect(publicListProjects).toHaveBeenCalledWith('johndoe')
    })
  })

  it('calls publicGetRanking with the username from params', async () => {
    vi.mocked(publicListProjects).mockResolvedValue([])
    render(<PublicProjectsPage />)
    await waitFor(() => {
      expect(publicGetRanking).toHaveBeenCalledWith('johndoe')
    })
  })

  it('shows Top projects and Insights link when ranking data exists', async () => {
    vi.mocked(publicListProjects).mockResolvedValue([
      { project_summary_id: 1, project_name: 'Project Alpha', project_type: null, project_mode: null, created_at: null },
      { project_summary_id: 2, project_name: 'Project Beta', project_type: null, project_mode: null, created_at: null },
    ])
    vi.mocked(publicGetRanking).mockResolvedValue([
      { rank: 1, project_summary_id: 1, project_name: 'Project Alpha' },
      { rank: 2, project_summary_id: 2, project_name: 'Project Beta' },
    ])
    render(<PublicProjectsPage />)
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Top projects' })).toBeInTheDocument()
    })
    const insightsLinks = screen
      .getAllByText('Insights')
      .map((el) => el.closest('a'))
      .filter((a): a is HTMLAnchorElement => !!a && a.getAttribute('href') === '/public/johndoe/insights')
    expect(insightsLinks.length).toBeGreaterThan(0)
  })

  it('renders Activity insights links with heatmap and project id for each top project', async () => {
    vi.mocked(publicListProjects).mockResolvedValue([
      { project_summary_id: 10, project_name: 'First', project_type: null, project_mode: null, created_at: null },
      { project_summary_id: 20, project_name: 'Second', project_type: null, project_mode: null, created_at: null },
    ])
    vi.mocked(publicGetRanking).mockResolvedValue([
      { rank: 1, project_summary_id: 10, project_name: 'First' },
      { rank: 2, project_summary_id: 20, project_name: 'Second' },
    ])
    render(<PublicProjectsPage />)
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Top projects' })).toBeInTheDocument()
    })
    const activityLinks = screen.getAllByRole('link', { name: /activity insights/i })
    expect(activityLinks).toHaveLength(2)
    expect(activityLinks[0]).toHaveAttribute(
      'href',
      '/public/johndoe/insights?view=activity-heatmap&project=10',
    )
    expect(activityLinks[1]).toHaveAttribute(
      'href',
      '/public/johndoe/insights?view=activity-heatmap&project=20',
    )
  })

  it('shows More projects when there are more than three public projects', async () => {
    vi.mocked(publicListProjects).mockResolvedValue([
      { project_summary_id: 1, project_name: 'P1', project_type: null, project_mode: null, created_at: null },
      { project_summary_id: 2, project_name: 'P2', project_type: null, project_mode: null, created_at: null },
      { project_summary_id: 3, project_name: 'P3', project_type: null, project_mode: null, created_at: null },
      { project_summary_id: 4, project_name: 'P4', project_type: null, project_mode: null, created_at: null },
    ])
    vi.mocked(publicGetRanking).mockResolvedValue([
      { rank: 1, project_summary_id: 1, project_name: 'P1' },
      { rank: 2, project_summary_id: 2, project_name: 'P2' },
      { rank: 3, project_summary_id: 3, project_name: 'P3' },
      { rank: 4, project_summary_id: 4, project_name: 'P4' },
    ])
    render(<PublicProjectsPage />)
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'More projects' })).toBeInTheDocument()
    })
    expect(screen.getByText('P4')).toBeInTheDocument()
    const activityLinks = screen.getAllByRole('link', { name: /activity insights/i })
    expect(activityLinks).toHaveLength(3)
  })

  it('shows All projects heading when ranking is empty', async () => {
    vi.mocked(publicListProjects).mockResolvedValue([
      { project_summary_id: 1, project_name: 'Solo', project_type: null, project_mode: null, created_at: null },
    ])
    vi.mocked(publicGetRanking).mockResolvedValue([])
    render(<PublicProjectsPage />)
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'All projects' })).toBeInTheDocument()
    })
    expect(screen.queryByRole('heading', { name: 'Top projects' })).not.toBeInTheDocument()
  })

  it('still loads projects when publicGetRanking fails', async () => {
    vi.mocked(publicListProjects).mockResolvedValue([
      { project_summary_id: 1, project_name: 'Only', project_type: null, project_mode: null, created_at: null },
    ])
    vi.mocked(publicGetRanking).mockRejectedValue(new Error('ranking unavailable'))
    render(<PublicProjectsPage />)
    await waitFor(() => {
      expect(screen.getByText('Only')).toBeInTheDocument()
    })
    expect(screen.getByRole('heading', { name: 'All projects' })).toBeInTheDocument()
  })
})
