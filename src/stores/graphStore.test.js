import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useGraphStore } from './graphStore.js'

describe('graphStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('getContinent returns correct continent for coordinates', () => {
    const store = useGraphStore()
    expect(store.getContinent(39.9, 116.4)).toBe('亚洲')
    expect(store.getContinent(48.9, 2.3)).toBe('欧洲')
    expect(store.getContinent(-25.3, 134.5)).toBe('大洋洲')
    expect(store.getContinent(41.9, -87.6)).toBe('北美洲')
    expect(store.getContinent(-23.6, -46.6)).toBe('南美洲')
    expect(store.getContinent(-1.3, 36.8)).toBe('非洲')
    expect(store.getContinent(-82.9, 0)).toBe('南极洲')
  })

  it('getContinent returns 未知 for null coords', () => {
    const store = useGraphStore()
    expect(store.getContinent(null, null)).toBe('未知')
  })
})
