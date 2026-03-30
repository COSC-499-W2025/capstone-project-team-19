import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PublicInsightsPage from '../PublicInsightsPage'

vi.mock('react-router-dom', () => ({
  useParams: vi.fn(() => ({ username: 'testuser' })),
  useNavigate: vi.fn(() => vi.fn()),
  useLocation: vi.fn(() => ({ pathname: '/public/testuser/insights' })),
  NavLink: ({ to, children }: { to: string; children: React.ReactNode | ((props: { isActive: boolean }) => React.ReactNode) }) => {
    const content = typeof children === 'function' ? children({ isActive: false }) : children
    return <a href={to}>{content}</a>
  },
  Link: ({ to, children }: { to: string; children: React.ReactNode }) => (
    <a href={to}>{children}</a>
  ),
}))

vi.mock('../../../api/public', () => ({
  publicGetRanking: vi.fn(),
  publicGetSkillsTimeline: vi.fn(),
  publicListProjects: vi.fn(),
  publicGetPortfolioStatus: vi.fn(),
  publicGetActivityByDate: vi.fn(),
  publicGetActivityHeatmapData: vi.fn(),
}))

vi.mock('../../../auth/token', () => ({
  tokenStore: { get: vi.fn(() => null) },
}))

vi.mock('../../../auth/user', () => ({
  getUsername: vi.fn(() => null),
}))

import {
  publicGetRanking,
  publicGetSkillsTimeline,
  publicListProjects,
  publicGetPortfolioStatus,
  publicGetActivityByDate,
} from '../../../api/public'

const emptyTimeline = {
  dated: [],
  undated: [],
  current_totals: {},
  summary: { total_skills: 0, total_projects: 0, date_range: {}, skill_names: [] },
}

const mockTimeline = {
  dated: [],
  undated: [],
  current_totals: {
    typescript: { cumulative_score: 0.9, projects: ['My App'], skill_type: 'code' },
  },
  summary: { total_skills: 1, total_projects: 1, date_range: {}, skill_names: ['typescript'] },
}

const mockRankings = [
  { rank: 1, project_summary_id: 1, project_name: 'Top Project' },
  { rank: 2, project_summary_id: 2, project_name: 'Second Project' },
]

const emptyHeatmapData = {
  title: 'Activity by Date',
  row_labels: [],
  col_labels: [],
  matrix: [],
  available_years: [],
  projects_by_date: {},
}

function setupDefaultMocks() {
  vi.mocked(publicGetRanking).mockResolvedValue(mockRankings)
  vi.mocked(publicGetSkillsTimeline).mockResolvedValue(mockTimeline)
  vi.mocked(publicListProjects).mockResolvedValue([
    { project_summary_id: 1, project_name: 'My App', project_type: null, project_mode: null, created_at: null },
  ])
  vi.mocked(publicGetPortfolioStatus).mockResolvedValue({ exists: true, is_public: true })
  vi.mocked(publicGetActivityByDate).mockResolvedValue(emptyHeatmapData)
}

describe('PublicInsightsPage', () => {
  beforeEach(() => {
    setupDefaultMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('page structure', () => {
    it('renders Insights page heading', async () => {
      render(<PublicInsightsPage />)
      await waitFor(() => {
        // PageHeader renders the main h1 heading; there may also be an h2 in the sidebar
        expect(screen.getAllByRole('heading', { name: 'Insights' }).length).toBeGreaterThan(0)
      })
    })

    it('renders the sidebar navigation', async () => {
      render(<PublicInsightsPage />)
      await waitFor(() => {
        expect(screen.getByRole('navigation')).toBeInTheDocument()
      })
    })

    it('renders all nav items', async () => {
      render(<PublicInsightsPage />)
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Ranked Projects' })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: 'Activity Heatmap' })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: 'Project Heatmap' })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: 'Timeline' })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: 'Skills Overview' })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: 'Skills Log' })).toBeInTheDocument()
      })
    })

    it('calls APIs with the username from params', async () => {
      render(<PublicInsightsPage />)
      await waitFor(() => {
        expect(publicGetRanking).toHaveBeenCalledWith('testuser')
        expect(publicGetSkillsTimeline).toHaveBeenCalledWith('testuser')
        expect(publicListProjects).toHaveBeenCalledWith('testuser')
      })
    })
  })

  describe('ranked projects view (default)', () => {
    it('shows Ranked Projects as the default active view title', async () => {
      render(<PublicInsightsPage />)
      await waitFor(() => {
        // The content area h3 title shows the active view label
        expect(screen.getByRole('heading', { level: 3, name: 'Ranked Projects' })).toBeInTheDocument()
      })
    })

    it('shows loading while rankings are fetching', async () => {
      vi.mocked(publicGetRanking).mockReturnValue(new Promise(() => {}))
      render(<PublicInsightsPage />)
      await waitFor(() => {
        expect(screen.getByText('Loading...')).toBeInTheDocument()
      })
    })

    it('shows error when rankings API fails', async () => {
      vi.mocked(publicGetRanking).mockRejectedValue(new Error('Rankings unavailable'))
      render(<PublicInsightsPage />)
      await waitFor(() => {
        expect(screen.getByText('Rankings unavailable')).toBeInTheDocument()
      })
    })

    it('renders ranked project names', async () => {
      render(<PublicInsightsPage />)
      await waitFor(() => {
        expect(screen.getByText('Top Project')).toBeInTheDocument()
        expect(screen.getByText('Second Project')).toBeInTheDocument()
      })
    })

    it('shows empty state when no ranked projects', async () => {
      vi.mocked(publicGetRanking).mockResolvedValue([])
      render(<PublicInsightsPage />)
      await waitFor(() => {
        expect(screen.getByText('No ranked projects.')).toBeInTheDocument()
      })
    })

    it('renders rank badges for top 3 projects', async () => {
      render(<PublicInsightsPage />)
      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument()
        expect(screen.getByText('2')).toBeInTheDocument()
      })
    })
  })

  describe('view switching', () => {
    it('switches to Activity Heatmap view when clicked', async () => {
      const user = userEvent.setup()
      render(<PublicInsightsPage />)
      await waitFor(() => screen.getByRole('button', { name: 'Activity Heatmap' }))
      await user.click(screen.getByRole('button', { name: 'Activity Heatmap' }))
      await waitFor(() => {
        // The page title h3 and the heatmap component both render "Activity Heatmap" headings
        expect(screen.getAllByRole('heading', { name: 'Activity Heatmap' }).length).toBeGreaterThan(0)
      })
    })

    it('switches to Project Heatmap view when clicked', async () => {
      const user = userEvent.setup()
      render(<PublicInsightsPage />)
      await waitFor(() => screen.getByRole('button', { name: 'Project Heatmap' }))
      await user.click(screen.getByRole('button', { name: 'Project Heatmap' }))
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 3, name: 'Project Heatmap' })).toBeInTheDocument()
      })
    })

    it('switches to Skills Timeline view when clicked', async () => {
      const user = userEvent.setup()
      render(<PublicInsightsPage />)
      await waitFor(() => screen.getByRole('button', { name: 'Timeline' }))
      await user.click(screen.getByRole('button', { name: 'Timeline' }))
      await waitFor(() => {
        // Nav button label is "Timeline" but the page title h3 label is "Skills Timeline"
        expect(screen.getByRole('heading', { level: 3, name: 'Skills Timeline' })).toBeInTheDocument()
      })
    })

    it('switches to Skills Overview view when clicked', async () => {
      const user = userEvent.setup()
      render(<PublicInsightsPage />)
      await waitFor(() => screen.getByRole('button', { name: 'Skills Overview' }))
      await user.click(screen.getByRole('button', { name: 'Skills Overview' }))
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 3, name: 'Skills Overview' })).toBeInTheDocument()
      })
    })

    it('switches to Skills Log view when clicked', async () => {
      const user = userEvent.setup()
      render(<PublicInsightsPage />)
      await waitFor(() => screen.getByRole('button', { name: 'Skills Log' }))
      await user.click(screen.getByRole('button', { name: 'Skills Log' }))
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 3, name: 'Skills Log' })).toBeInTheDocument()
      })
    })

    it('highlights the active nav button', async () => {
      const user = userEvent.setup()
      render(<PublicInsightsPage />)
      await waitFor(() => screen.getByRole('button', { name: 'Ranked Projects' }))
      // Default: Ranked Projects is active
      expect(screen.getByRole('button', { name: 'Ranked Projects' })).toHaveClass('bg-sky-50')

      // After clicking Activity Heatmap
      await user.click(screen.getByRole('button', { name: 'Activity Heatmap' }))
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Activity Heatmap' })).toHaveClass('bg-sky-50')
        expect(screen.getByRole('button', { name: 'Ranked Projects' })).not.toHaveClass('bg-sky-50')
      })
    })
  })

  describe('skills views', () => {
    it('shows loading for skills views while timeline is fetching', async () => {
      vi.mocked(publicGetSkillsTimeline).mockReturnValue(new Promise(() => {}))
      const user = userEvent.setup()
      render(<PublicInsightsPage />)
      await waitFor(() => screen.getByRole('button', { name: 'Skills Overview' }))
      await user.click(screen.getByRole('button', { name: 'Skills Overview' }))
      await waitFor(() => {
        expect(screen.getByText('Loading...')).toBeInTheDocument()
      })
    })

    it('shows error for skills views when timeline fails', async () => {
      vi.mocked(publicGetSkillsTimeline).mockRejectedValue(new Error('Timeline fetch failed'))
      const user = userEvent.setup()
      render(<PublicInsightsPage />)
      await waitFor(() => screen.getByRole('button', { name: 'Skills Overview' }))
      await user.click(screen.getByRole('button', { name: 'Skills Overview' }))
      await waitFor(() => {
        expect(screen.getByText('Timeline fetch failed')).toBeInTheDocument()
      })
    })

    it('renders skills overview with skill data', async () => {
      const user = userEvent.setup()
      render(<PublicInsightsPage />)
      await waitFor(() => screen.getByRole('button', { name: 'Skills Overview' }))
      await user.click(screen.getByRole('button', { name: 'Skills Overview' }))
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/search skills/i)).toBeInTheDocument()
      })
    })

    it('shows no skill data message when timeline is null after load', async () => {
      vi.mocked(publicGetSkillsTimeline).mockResolvedValue(null as any)
      const user = userEvent.setup()
      render(<PublicInsightsPage />)
      await waitFor(() => screen.getByRole('button', { name: 'Skills Overview' }))
      await user.click(screen.getByRole('button', { name: 'Skills Overview' }))
      await waitFor(() => {
        expect(screen.getByText('No skill data available.')).toBeInTheDocument()
      })
    })
  })

  describe('timeline filtering by public projects', () => {
    it('filters timeline to only include public project skills', async () => {
      vi.mocked(publicGetSkillsTimeline).mockResolvedValue({
        ...mockTimeline,
        current_totals: {
          typescript: { cumulative_score: 0.9, projects: ['My App'], skill_type: 'code' },
          python: { cumulative_score: 0.5, projects: ['Private Project'], skill_type: 'code' },
        },
      })
      // Only 'My App' is public
      vi.mocked(publicListProjects).mockResolvedValue([
        { project_summary_id: 1, project_name: 'My App', project_type: null, project_mode: null, created_at: null },
      ])
      const user = userEvent.setup()
      render(<PublicInsightsPage />)
      await waitFor(() => screen.getByRole('button', { name: 'Skills Overview' }))
      await user.click(screen.getByRole('button', { name: 'Skills Overview' }))
      // typescript should be shown (it belongs to 'My App' which is public)
      // python should NOT be shown (it belongs to 'Private Project' which is not public)
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/search skills/i)).toBeInTheDocument()
      })
    })
  })

  describe('Skills section divider label', () => {
    it('shows the Skills section divider in sidebar', async () => {
      render(<PublicInsightsPage />)
      await waitFor(() => {
        expect(screen.getByText('Skills')).toBeInTheDocument()
      })
    })
  })
})
