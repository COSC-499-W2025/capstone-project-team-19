import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import PublicProjectsPage from '../PublicProjects'

vi.mock('react-router-dom', () => ({
  useParams: vi.fn(() => ({ username: 'johndoe' })),
  useNavigate: vi.fn(() => vi.fn()),
  useLocation: vi.fn(() => ({ pathname: '/public/johndoe/projects' })),
  NavLink: ({ to, children }: { to: string; children: React.ReactNode | ((props: { isActive: boolean }) => React.ReactNode) }) => {
    const content = typeof children === 'function' ? children({ isActive: false }) : children
    return <a href={to}>{content}</a>
  },
  Link: ({ to, children }: { to: string; children: React.ReactNode }) => (
    <a href={to}>{children}</a>
  ),
}))

vi.mock('../../../api/public', () => ({
  publicListProjects: vi.fn(),
  publicFetchThumbnailUrl: vi.fn(),
}))

vi.mock('../../../auth/token', () => ({
  tokenStore: { get: vi.fn(() => null) },
}))

vi.mock('../../../auth/user', () => ({
  getUsername: vi.fn(() => null),
}))

import { publicListProjects, publicFetchThumbnailUrl } from '../../../api/public'

describe('PublicProjectsPage', () => {
  beforeEach(() => {
    vi.mocked(publicFetchThumbnailUrl).mockResolvedValue(null)
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
})
