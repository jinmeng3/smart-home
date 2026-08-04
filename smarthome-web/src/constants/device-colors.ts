export type DeviceCategory =
  "light" | "climate" | "lock" | "camera" | "energy" | "air";

export const deviceColorMap: Record<DeviceCategory, string> = {
  light: "text-[var(--color-device-light)]",
  climate: "text-[var(--color-device-climate)]",
  lock: "text-[var(--color-device-lock)]",
  camera: "text-[var(--color-device-camera)]",
  energy: "text-[var(--color-device-energy)]",
  air: "text-[var(--color-device-air)]",
};
