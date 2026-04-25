/**
 * 日志模块
 */

type LogLevel = "debug" | "info" | "warn" | "error";

interface Logger {
  debug(msg: string, ...args: unknown[]): void;
  info(msg: string, ...args: unknown[]): void;
  warn(msg: string, ...args: unknown[]): void;
  error(msg: string, ...args: unknown[]): void;
}

/** 控制台颜色码 */
const COLORS = {
  reset: "\x1b[0m",
  dim: "\x1b[2m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  red: "\x1b[31m",
} as const;

function formatMessage(level: LogLevel, msg: string): string {
  const timestamp = new Date().toISOString();
  const color = level === "error" ? COLORS.red : level === "warn" ? COLORS.yellow : COLORS.green;
  return `${COLORS.dim}[${timestamp}]${COLORS.reset} ${color}[${level.toUpperCase()}]${COLORS.reset} ${msg}`;
}

/** 默认日志记录器 */
export const logger: Logger = {
  debug(msg: string, ...args: unknown[]) {
    console.debug(formatMessage("debug", msg), ...args);
  },
  info(msg: string, ...args: unknown[]) {
    console.info(formatMessage("info", msg), ...args);
  },
  warn(msg: string, ...args: unknown[]) {
    console.warn(formatMessage("warn", msg), ...args);
  },
  error(msg: string, ...args: unknown[]) {
    console.error(formatMessage("error", msg), ...args);
  },
};
