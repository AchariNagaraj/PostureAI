// src/__tests__/useCamera.test.js
import { renderHook, act } from '@testing-library/react';
import { useCamera, CameraStatus } from '../hooks/useCamera';
import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';

describe('useCamera hook', () => {
  beforeAll(() => {
    // Mock getUserMedia
    global.navigator.mediaDevices = {
      getUserMedia: vi.fn(() =>
        Promise.resolve({
          getTracks: () => [{ stop: vi.fn() }],
        })
      ),
    };
  });

  afterAll(() => {
    delete global.navigator.mediaDevices;
  });

  it('starts camera successfully', async () => {
    const { result } = renderHook(() => useCamera());
    await act(async () => {
      await result.current.start();
    });
    expect(result.current.status).toBe(CameraStatus.ACTIVE);
    expect(result.current.stream).not.toBeNull();
  });

  it('handles permission denied', async () => {
    global.navigator.mediaDevices.getUserMedia.mockImplementationOnce(() =>
      Promise.reject(new Error('Permission denied'))
    );
    const { result } = renderHook(() => useCamera());
    await act(async () => {
      await result.current.start();
    });
    expect(result.current.status).toBe(CameraStatus.ERROR);
    expect(result.current.error).toContain('Permission denied');
  });
});
