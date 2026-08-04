export type SemanticStatus =
  "online" | "offline" | "running" | "warning" | "error" | "success";

export interface StatusColorConfig {
  textClass: string;
  backgroundClass: string;
  borderClass: string;
  dotClass: string;
}

export const statusColorMap: Record<SemanticStatus, StatusColorConfig> = {
  online: {
    textClass: "text-[var(--color-success)]",
    backgroundClass: "bg-[var(--color-success-soft)]",
    borderClass: "border-[var(--color-success-border)]",
    dotClass: "bg-[var(--color-success)]",
  },
  offline: {
    textClass: "text-[var(--color-text-tertiary)]",
    backgroundClass: "bg-[var(--color-surface-subtle)]",
    borderClass: "border-[var(--color-border-default)]",
    dotClass: "bg-[var(--color-text-muted)]",
  },
  running: {
    textClass: "text-[var(--color-info)]",
    backgroundClass: "bg-[var(--color-info-soft)]",
    borderClass: "border-[var(--color-info-border)]",
    dotClass: "bg-[var(--color-info)]",
  },
  warning: {
    textClass: "text-[var(--color-warning)]",
    backgroundClass: "bg-[var(--color-warning-soft)]",
    borderClass: "border-[var(--color-warning-border)]",
    dotClass: "bg-[var(--color-warning)]",
  },
  error: {
    textClass: "text-[var(--color-danger)]",
    backgroundClass: "bg-[var(--color-danger-soft)]",
    borderClass: "border-[var(--color-danger-border)]",
    dotClass: "bg-[var(--color-danger)]",
  },
  success: {
    textClass: "text-[var(--color-success)]",
    backgroundClass: "bg-[var(--color-success-soft)]",
    borderClass: "border-[var(--color-success-border)]",
    dotClass: "bg-[var(--color-success)]",
  },
};
