import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import PublicInsightsPage from '../PublicInsightsPage'

vi.mock('../PublicLayout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid="layout">{children}</div>,
}))

vi.mock('../../../api/public', () => ({
  publicGetRanking: vi.fn(() => Promise.resolve([])),
  publicGetSkillsTimeline: vi.fn(() => Promise.resolve(null)),
  publicListProjects: vi.fn(() => Promise.resolve([])),
}))

vi.mock('../../../components/insights/tabs/Projects/PublicActivityHeatmapTab', () => ({
  default: ({ initialProjectId }: { initialProjectId?: number }) => (
    <div
      data-testid="activity-heatmap-mock"
      data-initial-project={initialProjectId === undefined ? '' : String(initialProjectId)}
    />
  ),
}))

import { publicGetRanking, publicGetSkillsTimeline, publicListProjects } from '../../../api/public'

function renderInsights(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/public/:username/insights" element={<PublicInsightsPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('PublicInsightsPage', () => {
  beforeEach(() => {
    vi.mocked(publicGetRanking).mockResolvedValue([
      { rank: 1, project_summary_id: 1, project_name: 'A' },
    ])
    vi.mocked(publicGetSkillsTimeline).mockResolvedValue({
      skills: [],
    } as unknown as Awaited<ReturnType<typeof publicGetSkillsTimeline>>)
    vi.mocked(publicListProjects).mockResolvedValue([])
  })

  it('passes initialProjectId from ?project= when view=activity-heatmap', async () => {
    renderInsights('/public/johndoe/insights?view=activity-heatmap&project=42')
    await waitFor(() => {
      const el = screen.getByTestId('activity-heatmap-mock')
      expect(el).toHaveAttribute('data-initial-project', '42')
    })
    expect(screen.getByRole('heading', { name: 'Activity Heatmap' })).toBeInTheDocument()
  })

  it('defaults to ranked projects when view param is missing', async () => {
    renderInsights('/public/johndoe/insights')
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Ranked Projects' })).toBeInTheDocument()
    })
    expect(screen.queryByTestId('activity-heatmap-mock')).not.toBeInTheDocument()
  })
})
