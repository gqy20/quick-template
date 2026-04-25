/**
 * API 路由（Hono）
 */
import { Hono } from "hono";

export const app = new Hono();

// 健康检查
app.get("/api/v1/health", (c) => {
  return c.json({
    code: 0,
    data: null,
    message: "ok",
  });
});

// TODO: 注册更多路由
