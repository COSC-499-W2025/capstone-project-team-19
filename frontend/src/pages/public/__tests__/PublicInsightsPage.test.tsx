import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('react-router-dom', () => ({
  useParams: vi.fn(() => ({ username: 'johndoe' })),
}))

vi.mock('../../../api/public', () => ({
  publicGetRanking: vi.fn(),
  publicGetSkillsTimeline: vi.fn(),
}))

vi.mock('../PublicLayout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid="public-layout">{children}</div>,
}))

vi.mock('../../../components/insights/tabs/Skills/SkillsOverview', () => ({
  default: () => <div data-testid="skills-overview" />,
}))

vi.mock('../../../components/insights/tabs/Skills/SkillProgressChart', () => ({
  default: () => <div data-testid="skill-progress-chart" />,
}))

vi.mock('../../../components/insights/tabs/Skills/SkillsTimeline', () => ({
  default: () => <div data-testid="skills-timeline" />,
}))

vi.mock('../../../components/insights/tabs/Skills/SkillsLog', () => ({
  default: () => <div data-testid="skills-log" />,
}))

vi.mock('../../../components/insights/tabs/Projects/PublicActivityHeatmapTab', () => ({
  default: () => <div data-testid="activity-heatmap-tab" />,
}))

vi.mock('../../../components/insights/tabs/Projects/PublicProjectSkillHeatmapTab', () => ({
  default: () => <div data-testid="project-heatmap-tab" />,
}))

import PublicInsightsPage from '../PublicInsightsPage'
import { publicGetRanking, publicGetSkillsTimeline } from '../../../api/public'

const mockRankings = [
  { rank: 1, project_summary_id: 1, project_name: 'Alpha Project' },
  { rank: 2, project_summary_id: 2, project_name: 'Beta Project' },
  { rank: 3, project_summary_id: 3, project_name: 'Gamma Project' },
  { rank: 4, project_summary_id: 4, project_name: 'Delta Project' },
]

const mockTimeline = {
  skills: [
    {
      skill_name: 'Python',
      level: 'intermediate',
      entries: [],
    },
  ],
}

describe('PublicInsightsPage', () => {
  beforeEach(() => {
    vi.mocked(publicGetRanking).mockResolvedValue(mockRankings)
    vi.mocked(publicGetSkillsTimeline).mockResolvedValue(mockTimeline as never)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state while fetching ranked projects', () => {
    vi.mocked(publicGetRanking).mockReturnValue(new Promise(() => {}))
    vi.mocked(publicGetSkillsTimeline).mockReturnValue(new Promise(() => {}))
    render(<PublicInsightsPage />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders inside PublicLayout', async () => {
    render(<PublicInsightsPage />)
    expect(screen.getByTestId('public-layout')).toBeInTheDocument()
  })

  it('renders all sidebar navigation items', async () => {
    render(<PublicInsightsPage />)
    expect(screen.getByRole('button', { name: 'Ranked Projects' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Activity Heatmap' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Project Heatmap' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Skills Overview' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Skills Timeline' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Skills Log' })).toBeInTheDocument()
  })

  it('renders ranked projects by default', async () => {
    render(<PublicInsightsPage />)
    await waitFor(() => {
      expect(screen.getByText('Alpha Project')).toBeInTheDocument()
    })
    expect(screen.getByText('Beta Project')).toBeInTheDocument()
    expect(screen.getByText('Gamma Project')).toBeInTheDocument()
    expect(screen.getByText('Delta Project')).toBeInTheDocument()
  })

  it('shows "Ranked Projects" as the active page title by default', async () => {
    render(<PublicInsightsPage />)
    expect(screen.getByRole('heading', { name: 'Ranked Projects' })).toBeInTheDocument()
  })

  it('shows empty message when no ranked projects', async () => {
    vi.mocked(publicGetRanking).mockResolvedValue([])
    render(<PublicInsightsPage />)
    await waitFor(() => {
      expect(screen.getByText('No ranked projects.')).toBeInTheDocument()
    })
  })

  it('shows error message when rankings fetch fails', async () => {
    vi.mocked(publicGetRanking).mockRejectedValue(new Error('Failed to load rankings'))
    render(<PublicInsightsPage />)
    await waitFor(() => {
      expect(screen.getByText('Failed to load rankings')).toBeInTheDocument()
    })
  })

  it('calls publicGetRanking with the username from route params', async () => {
    render(<PublicInsightsPage />)
    await waitFor(() => {
      expect(publicGetRanking).toHaveBeenCalledWith('johndoe')
    })
  })

  it('calls publicGetSkillsTimeline with the username from route params', async () => {
    render(<PublicInsightsPage />)
    await waitFor(() => {
      expect(publicGetSkillsTimeline).toHaveBeenCalledWith('johndoe')
    })
  })

  it('navigates to Activity Heatmap view on click', async () => {
    const user = userEvent.setup()
    render(<PublicInsightsPage />)
    await user.click(screen.getByRole('button', { name: 'Activity Heatmap' }))
    expect(screen.getByTestId('activity-heatmap-tab')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Activity Heatmap' })).toBeInTheDocument()
  })

  it('navigates to Project Heatmap view on click', async () => {
    const user = userEvent.setup()
    render(<PublicInsightsPage />)
    await user.click(screen.getByRole('button', { name: 'Project Heatmap' }))
    expect(screen.getByTestId('project-heatmap-tab')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Project Heatmap' })).toBeInTheDocument()
  })

  it('navigates to Skills Overview view and renders component', async () => {
    const user = userEvent.setup()
    render(<PublicInsightsPage />)
    await user.click(screen.getByRole('button', { name: 'Skills Overview' }))
    await waitFor(() => {
      expect(screen.getByTestId('skills-overview')).toBeInTheDocument()
    })
    expect(screen.getByRole('heading', { name: 'Skills Overview' })).toBeInTheDocument()
  })

  it('navigates to Skills Timeline view and renders chart and timeline', async () => {
    const user = userEvent.setup()
    render(<PublicInsightsPage />)
    await user.click(screen.getByRole('button', { name: 'Skills Timeline' }))
    await waitFor(() => {
      expect(screen.getByTestId('skill-progress-chart')).toBeInTheDocument()
      expect(screen.getByTestId('skills-timeline')).toBeInTheDocument()
    })
  })

  it('navigates to Skills Log view and renders component', async () => {
    const user = userEvent.setup()
    render(<PublicInsightsPage />)
    await user.click(screen.getByRole('button', { name: 'Skills Log' }))
    await waitFor(() => {
      expect(screen.getByTestId('skills-log')).toBeInTheDocument()
    })
    expect(screen.getByRole('heading', { name: 'Skills Log' })).toBeInTheDocument()
  })

  it('shows loading state for skills views while timeline is pending', async () => {
    vi.mocked(publicGetSkillsTimeline).mockReturnValue(new Promise(() => {}))
    const user = userEvent.setup()
    render(<PublicInsightsPage />)
    await user.click(screen.getByRole('button', { name: 'Skills Overview' }))
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('shows timeline error when skills fetch fails', async () => {
    vi.mocked(publicGetSkillsTimeline).mockRejectedValue(new Error('Timeline fetch error'))
    const user = userEvent.setup()
    render(<PublicInsightsPage />)
    await user.click(screen.getByRole('button', { name: 'Skills Overview' }))
    await waitFor(() => {
      expect(screen.getByText('Timeline fetch error')).toBeInTheDocument()
    })
  })

  it('shows no skill data message when timeline is null', async () => {
    vi.mocked(publicGetSkillsTimeline).mockResolvedValue(null as never)
    const user = userEvent.setup()
    render(<PublicInsightsPage />)
    await user.click(screen.getByRole('button', { name: 'Skills Overview' }))
    await waitFor(() => {
      expect(screen.getByText('No skill data available.')).toBeInTheDocument()
    })
  })

  it('displays rank numbers for all projects', async () => {
    render(<PublicInsightsPage />)
    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getByText('4')).toBeInTheDocument()
    })
  })
})
