import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import PublicLayout from '../PublicLayout'

vi.mock('react-router-dom', () => ({
  useParams: vi.fn(() => ({ username: 'johndoe' })),
  NavLink: ({ to, children }: { to: string; children: React.ReactNode }) => (
    <a href={to}>{children}</a>
  ),
  Link: ({ to, children }: { to: string; children: React.ReactNode }) => (
    <a href={to}>{children}</a>
  ),
}))

vi.mock('../../../auth/token', () => ({
  tokenStore: { get: vi.fn() },
}))

vi.mock('../../../auth/user', () => ({
  getUsername: vi.fn(),
}))

import { tokenStore } from '../../../auth/token'
import { getUsername } from '../../../auth/user'

describe('PublicLayout', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders brand name', () => {
    vi.mocked(tokenStore.get).mockReturnValue(null)
    render(<PublicLayout><div /></PublicLayout>)
    expect(screen.getByText('resuME')).toBeInTheDocument()
  })

  it('renders nav links for Projects, Insights, and Outputs', () => {
    vi.mocked(tokenStore.get).mockReturnValue(null)
    render(<PublicLayout><div /></PublicLayout>)
    expect(screen.getByText('Projects')).toBeInTheDocument()
    expect(screen.getByText('Insights')).toBeInTheDocument()
    expect(screen.getByText('Outputs')).toBeInTheDocument()
  })

  it('shows "Viewing {username}\'s portfolio"', () => {
    vi.mocked(tokenStore.get).mockReturnValue(null)
    render(<PublicLayout><div /></PublicLayout>)
    expect(screen.getByText(/Viewing johndoe's portfolio/)).toBeInTheDocument()
  })

  it('renders children', () => {
    vi.mocked(tokenStore.get).mockReturnValue(null)
    render(<PublicLayout><div data-testid="child-content" /></PublicLayout>)
    expect(screen.getByTestId('child-content')).toBeInTheDocument()
  })

  it('shows logged-in username when user is logged in', () => {
    vi.mocked(tokenStore.get).mockReturnValue('some-token')
    vi.mocked(getUsername).mockReturnValue('currentuser')
    render(<PublicLayout><div /></PublicLayout>)
    expect(screen.getByText('currentuser')).toBeInTheDocument()
  })

  it('does not show logged-in user area when not logged in', () => {
    vi.mocked(tokenStore.get).mockReturnValue(null)
    vi.mocked(getUsername).mockReturnValue(null)
    render(<PublicLayout><div /></PublicLayout>)
    expect(screen.queryByText('currentuser')).not.toBeInTheDocument()
  })

  it('nav links point to the correct public URLs', () => {
    vi.mocked(tokenStore.get).mockReturnValue(null)
    render(<PublicLayout><div /></PublicLayout>)
    expect(screen.getByText('Projects').closest('a')).toHaveAttribute(
      'href',
      '/public/johndoe/projects',
    )
    expect(screen.getByText('Insights').closest('a')).toHaveAttribute(
      'href',
      '/public/johndoe/insights',
    )
    expect(screen.getByText('Outputs').closest('a')).toHaveAttribute(
      'href',
      '/public/johndoe/outputs',
    )
  })
})
