import { onScopeDispose } from 'vue'
import type { Device } from '../types/device'

export interface DeviceUpdate {
  id: string
  status?: string
  value?: string | number
  updatedAt?: string
  online?: boolean
}

type CommitDeviceUpdates = (updates: DeviceUpdate[]) => void

const isSameUpdate = (device: Device | undefined, update: DeviceUpdate) => {
  if (!device) {
    return false
  }

  return (
    (update.status === undefined || update.status === device.status) &&
    (update.value === undefined || String(update.value) === device.value) &&
    (update.updatedAt === undefined || update.updatedAt === device.updatedAt) &&
    (update.online === undefined || update.online === device.online)
  )
}

export const useBatchedDeviceUpdates = (commit: CommitDeviceUpdates, getDevice: (id: string) => Device | undefined) => {
  const pendingUpdates = new Map<string, DeviceUpdate>()
  let frameId = 0

  const flush = () => {
    frameId = 0
    const updates = Array.from(pendingUpdates.values()).filter((update) => !isSameUpdate(getDevice(update.id), update))
    pendingUpdates.clear()

    if (updates.length) {
      commit(updates)
    }
  }

  const schedule = () => {
    if (!frameId) {
      frameId = window.requestAnimationFrame(flush)
    }
  }

  const queueDeviceUpdate = (update: DeviceUpdate) => {
    pendingUpdates.set(update.id, {
      ...pendingUpdates.get(update.id),
      ...update,
    })
    schedule()
  }

  const queueDeviceUpdates = (updates: DeviceUpdate[]) => {
    updates.forEach(queueDeviceUpdate)
  }

  const dispose = () => {
    if (frameId) {
      window.cancelAnimationFrame(frameId)
      frameId = 0
    }

    pendingUpdates.clear()
  }

  onScopeDispose(dispose)

  return {
    dispose,
    queueDeviceUpdate,
    queueDeviceUpdates,
  }
}
