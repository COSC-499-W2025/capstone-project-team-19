import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import ProjectsPage from '../Projects'

vi.mock('../../api/projects', () => ({
    listProjects: vi.fn(),
    fetchThumbnailUrl: vi.fn(),
}))

vi.mock('../../auth/user', () => ({
    getUsername: vi.fn(() => 'testuser'),
}))

vi.mock('react-router-dom', () => ({
    useNavigate: vi.fn(() => vi.fn()),
}))

vi.mock('../../components/TopBar', () => ({
    default: () => <div data-testid="topbar" />,
}))

import { listProjects, fetchThumbnailUrl } from '../../api/projects'

describe('ProjectsPage', () => {
    beforeEach(() => {
        vi.mocked(fetchThumbnailUrl).mockResolvedValue(null)
    })

    afterEach(() => {
        vi.clearAllMocks()
    })

    it('shows loading state initially', () => {
        vi.mocked(listProjects).mockReturnValue(new Promise(() => {}))
        render(<ProjectsPage />)
        expect(screen.getByText('Loading…')).toBeInTheDocument()
    })

    it('renders project cards after successful load', async () => {
        vi.mocked(listProjects).mockResolvedValue([
            { project_summary_id: 1, project_name: 'Project Alpha', project_key: null, project_type: null, project_mode: null, created_at: null },
            { project_summary_id: 2, project_name: 'Project Beta', project_key: null, project_type: null, project_mode: null, created_at: null },
        ])
        render(<ProjectsPage />)
        await waitFor(() => {
            expect(screen.getByText('Project Alpha')).toBeInTheDocument()
            expect(screen.getByText('Project Beta')).toBeInTheDocument()
        })
    })

    it('shows empty state when no projects exist', async () => {
        vi.mocked(listProjects).mockResolvedValue([])
        render(<ProjectsPage />)
        await waitFor(() => {
            expect(screen.getByText(/No projects yet/)).toBeInTheDocument()
        })
    })

    it('shows error message when API fails', async () => {
        vi.mocked(listProjects).mockRejectedValue(new Error('Network error'))
        render(<ProjectsPage />)
        await waitFor(() => {
            expect(screen.getByText('Network error')).toBeInTheDocument()
        })
    })

    it('does not show empty state while loading', () => {
        vi.mocked(listProjects).mockReturnValue(new Promise(() => {}))
        render(<ProjectsPage />)
        expect(screen.queryByText(/No projects yet/)).not.toBeInTheDocument()
    })

    it('renders the page heading', async () => {
        vi.mocked(listProjects).mockResolvedValue([])
        render(<ProjectsPage />)
        expect(screen.getByText('Projects')).toBeInTheDocument()
    })
})
