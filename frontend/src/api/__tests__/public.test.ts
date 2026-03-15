import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

vi.mock('../client', () => ({
  api: {
    get: vi.fn(),
    getBlob: vi.fn(),
  },
}))

import { api } from '../client'
import {
  publicListProjects,
  publicGetProject,
  publicFetchThumbnailUrl,
  publicGetRanking,
  publicGetSkillsTimeline,
  publicListResumes,
  publicGetResume,
} from '../public'

describe('public API', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('publicListProjects', () => {
    it('calls the correct endpoint and returns projects', async () => {
      const projects = [{ project_summary_id: 1, project_name: 'Alpha' }]
      vi.mocked(api.get).mockResolvedValue({ success: true, data: { projects } })

      const result = await publicListProjects('johndoe')

      expect(api.get).toHaveBeenCalledWith('/public/johndoe/projects')
      expect(result).toEqual(projects)
    })
  })

  describe('publicGetProject', () => {
    it('calls the correct endpoint and returns project detail', async () => {
      const detail = { project_summary_id: 5, project_name: 'Beta', data: {} }
      vi.mocked(api.get).mockResolvedValue({ success: true, data: detail })

      const result = await publicGetProject('johndoe', 5)

      expect(api.get).toHaveBeenCalledWith('/public/johndoe/projects/5')
      expect(result).toEqual(detail)
    })
  })

  describe('publicFetchThumbnailUrl', () => {
    beforeEach(() => {
      vi.stubGlobal('URL', {
        createObjectURL: vi.fn(() => 'blob:mock-url'),
        revokeObjectURL: vi.fn(),
      })
    })

    afterEach(() => {
      vi.unstubAllGlobals()
    })

    it('returns an object URL when blob fetch succeeds', async () => {
      vi.mocked(api.getBlob).mockResolvedValue(new Blob(['img'], { type: 'image/png' }))

      const result = await publicFetchThumbnailUrl('johndoe', 3)

      expect(api.getBlob).toHaveBeenCalledWith('/public/johndoe/projects/3/thumbnail')
      expect(result).toBe('blob:mock-url')
    })

    it('returns null when blob fetch throws', async () => {
      vi.mocked(api.getBlob).mockRejectedValue(new Error('Not found'))

      const result = await publicFetchThumbnailUrl('johndoe', 3)

      expect(result).toBeNull()
    })
  })

  describe('publicGetRanking', () => {
    it('calls the correct endpoint', async () => {
      const ranking = { projects: [] }
      vi.mocked(api.get).mockResolvedValue(ranking)

      const result = await publicGetRanking('johndoe')

      expect(api.get).toHaveBeenCalledWith('/public/johndoe/ranking')
      expect(result).toEqual(ranking)
    })
  })

  describe('publicGetSkillsTimeline', () => {
    it('calls the correct endpoint', async () => {
      const timeline = { events: [] }
      vi.mocked(api.get).mockResolvedValue(timeline)

      const result = await publicGetSkillsTimeline('johndoe')

      expect(api.get).toHaveBeenCalledWith('/public/johndoe/skills/timeline')
      expect(result).toEqual(timeline)
    })
  })

  describe('publicListResumes', () => {
    it('calls the correct endpoint', async () => {
      const response = { data: { resumes: [] } }
      vi.mocked(api.get).mockResolvedValue(response)

      const result = await publicListResumes('johndoe')

      expect(api.get).toHaveBeenCalledWith('/public/johndoe/resumes')
      expect(result).toEqual(response)
    })
  })

  describe('publicGetResume', () => {
    it('calls the correct endpoint', async () => {
      const response = { data: { resume_id: 7 } }
      vi.mocked(api.get).mockResolvedValue(response)

      const result = await publicGetResume('johndoe', 7)

      expect(api.get).toHaveBeenCalledWith('/public/johndoe/resumes/7')
      expect(result).toEqual(response)
    })
  })
})
