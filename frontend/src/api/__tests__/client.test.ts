import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { api } from '../client'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

describe('api client', () => {
    it('exports get, postJson, and postForm methods', () => {
        expect(api).toHaveProperty('get')
        expect(api).toHaveProperty('postJson')
        expect(api).toHaveProperty('postForm')
        expect(typeof api.get).toBe('function')
        expect(typeof api.postJson).toBe('function')
        expect(typeof api.postForm).toBe('function')
    })

    describe('request behavior', () => {
        const mockFetch = vi.fn()

        beforeEach(() => {
            vi.stubGlobal('fetch', mockFetch)
            mockFetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({}),
                text: () => Promise.resolve(''),
            })
        })

        afterEach(() => {
            vi.unstubAllGlobals()
            localStorage.clear()
        })

        it('calls fetch with BASE_URL + path', async () => {
            await api.get('/users')

            expect(mockFetch).toHaveBeenCalledWith(
                `${BASE_URL}/users`,
                expect.objectContaining({
                    headers: expect.any(Object),
                })
            )
        })

        it('attaches Authorization header when token exists', async () => {
            localStorage.setItem('resuME_token', 'secret-123')
            await api.get('/me')

            expect(mockFetch).toHaveBeenCalledWith(
                expect.any(String),
                expect.objectContaining({
                    headers: expect.objectContaining({
                        Authorization: 'Bearer secret-123',
                    }),
                })
            )
        })

        it('does not attach Authorization header when no token', async () => {
            await api.get('/public')

            expect(mockFetch).toHaveBeenCalledWith(
                expect.any(String),
                expect.objectContaining({
                    headers: expect.not.objectContaining({
                        Authorization: expect.any(String),
                    }),
                })
            )
        })
    })
})
