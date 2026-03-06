import { describe, it, expect } from 'vitest'
import { api } from '../client'

describe('api client', () => {
    it('exports get, postJson, and postForm methods', () => {
        expect(api).toHaveProperty('get')
        expect(api).toHaveProperty('postJson')
        expect(api).toHaveProperty('postForm')
        expect(typeof api.get).toBe('function')
        expect(typeof api.postJson).toBe('function')
        expect(typeof api.postForm).toBe('function')
    })
})
