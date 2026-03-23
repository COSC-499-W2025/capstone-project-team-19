import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

vi.mock('react-router-dom', () => ({
  useParams: vi.fn(() => ({ username: 'johndoe' })),
}))

vi.mock('../../../api/public', () => ({
  publicGetActiveResume: vi.fn(),
  publicDownloadResumeDocx: vi.fn(),
  publicDownloadResumePdf: vi.fn(),
}))

vi.mock('../PublicLayout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid="public-layout">{children}</div>,
}))

vi.mock('../../../components/outputs/ExportDropdown', () => ({
  default: ({ onDocx, onPdf }: { onDocx: () => void; onPdf: () => void }) => (
    <div data-testid="export-dropdown">
      <button onClick={onDocx}>Export DOCX</button>
      <button onClick={onPdf}>Export PDF</button>
    </div>
  ),
}))

import PublicOutputsPage from '../PublicOutputsPage'
import { publicGetActiveResume, publicDownloadResumeDocx, publicDownloadResumePdf } from '../../../api/public'

const mockResume = {
  id: 42,
  name: 'My Portfolio Resume',
  created_at: '2024-01-01T00:00:00Z',
  projects: [
    {
      project_name: 'Project Alpha',
      project_type: 'Software',
      project_mode: 'Team',
      languages: ['TypeScript'],
      frameworks: ['React'],
      summary_text: 'A great project',
      skills: ['Testing'],
      key_role: 'Frontend Developer',
      contribution_bullets: ['Built UI components', 'Wrote tests'],
      start_date: '2023-01-01',
      end_date: '2023-06-30',
    },
    {
      project_name: 'Project Beta',
      project_type: 'Research',
      project_mode: 'Solo',
      languages: ['Python'],
      frameworks: [],
      summary_text: null,
      skills: [],
      key_role: 'Researcher',
      contribution_bullets: ['Conducted analysis'],
      start_date: '2022-01-01',
      end_date: '2022-12-31',
    },
  ],
  aggregated_skills: {
    languages: ['TypeScript', 'Python'],
    frameworks: ['React'],
    technical_skills: ['Git', 'Docker'],
    writing_skills: ['Technical Writing'],
  },
  rendered_text: null,
}

describe('PublicOutputsPage', () => {
  beforeEach(() => {
    vi.mocked(publicGetActiveResume).mockResolvedValue(mockResume)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders inside PublicLayout', () => {
    vi.mocked(publicGetActiveResume).mockReturnValue(new Promise(() => {}))
    render(<PublicOutputsPage />)
    expect(screen.getByTestId('public-layout')).toBeInTheDocument()
  })

  it('shows loading state while fetching resume', () => {
    vi.mocked(publicGetActiveResume).mockReturnValue(new Promise(() => {}))
    render(<PublicOutputsPage />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('shows error message when fetch fails', async () => {
    vi.mocked(publicGetActiveResume).mockRejectedValue(new Error('Failed to fetch resume'))
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByText('Failed to fetch resume')).toBeInTheDocument()
    })
  })

  it('shows no resume message when active resume is null', async () => {
    vi.mocked(publicGetActiveResume).mockResolvedValue(null)
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByText('No resume has been set for this portfolio.')).toBeInTheDocument()
    })
  })

  it('calls publicGetActiveResume with username from route params', async () => {
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(publicGetActiveResume).toHaveBeenCalledWith('johndoe')
    })
  })

  it('renders resume name as heading', async () => {
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'My Portfolio Resume' })).toBeInTheDocument()
    })
  })

  it('renders ExportDropdown when resume is loaded', async () => {
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByTestId('export-dropdown')).toBeInTheDocument()
    })
  })

  it('renders aggregated languages', async () => {
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByText(/Languages:/)).toBeInTheDocument()
      expect(screen.getByText(/TypeScript, Python/)).toBeInTheDocument()
    })
  })

  it('renders aggregated frameworks', async () => {
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByText(/Frameworks:/)).toBeInTheDocument()
      expect(screen.getByText(/React/)).toBeInTheDocument()
    })
  })

  it('renders aggregated technical skills', async () => {
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByText(/Technical skills:/)).toBeInTheDocument()
      expect(screen.getByText(/Git, Docker/)).toBeInTheDocument()
    })
  })

  it('renders aggregated writing skills', async () => {
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByText(/Writing skills:/)).toBeInTheDocument()
      expect(screen.getByText(/Technical Writing/)).toBeInTheDocument()
    })
  })

  it('renders all project names', async () => {
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByText('Project Alpha')).toBeInTheDocument()
      expect(screen.getByText('Project Beta')).toBeInTheDocument()
    })
  })

  it('renders project key role and date range', async () => {
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByText(/Frontend Developer/)).toBeInTheDocument()
      expect(screen.getByText(/Jun 2023/)).toBeInTheDocument()
    })
  })

  it('renders contribution bullets as list items', async () => {
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByText('Built UI components')).toBeInTheDocument()
      expect(screen.getByText('Wrote tests')).toBeInTheDocument()
    })
  })

  it('renders projects sorted by end date descending', async () => {
    render(<PublicOutputsPage />)
    await waitFor(() => {
      const projectNames = screen.getAllByRole('heading', { level: 4 }).map((h) => h.textContent)
      expect(projectNames.indexOf('Project Alpha')).toBeLessThan(projectNames.indexOf('Project Beta'))
    })
  })

  it('calls publicDownloadResumeDocx when Export DOCX is clicked', async () => {
    vi.mocked(publicDownloadResumeDocx).mockResolvedValue(undefined)
    const { getByRole } = render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByTestId('export-dropdown')).toBeInTheDocument()
    })
    getByRole('button', { name: 'Export DOCX' }).click()
    expect(publicDownloadResumeDocx).toHaveBeenCalledWith('johndoe', 42)
  })

  it('calls publicDownloadResumePdf when Export PDF is clicked', async () => {
    vi.mocked(publicDownloadResumePdf).mockResolvedValue(undefined)
    const { getByRole } = render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByTestId('export-dropdown')).toBeInTheDocument()
    })
    getByRole('button', { name: 'Export PDF' }).click()
    expect(publicDownloadResumePdf).toHaveBeenCalledWith('johndoe', 42)
  })

  it('does not render Skills section labels when all skill categories are empty', async () => {
    vi.mocked(publicGetActiveResume).mockResolvedValue({
      ...mockResume,
      aggregated_skills: {
        languages: [],
        frameworks: [],
        technical_skills: [],
        writing_skills: [],
      },
    })
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.queryByText(/Languages:/)).not.toBeInTheDocument()
      expect(screen.queryByText(/Frameworks:/)).not.toBeInTheDocument()
      expect(screen.queryByText(/Technical skills:/)).not.toBeInTheDocument()
      expect(screen.queryByText(/Writing skills:/)).not.toBeInTheDocument()
    })
  })

  it('renders "Present" for project with no end date', async () => {
    vi.mocked(publicGetActiveResume).mockResolvedValue({
      ...mockResume,
      projects: [
        {
          ...mockResume.projects[0],
          end_date: null,
          start_date: '2024-03-01',
        },
      ],
    })
    render(<PublicOutputsPage />)
    await waitFor(() => {
      expect(screen.getByText(/Present/)).toBeInTheDocument()
    })
  })
})
