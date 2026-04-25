{% if add_api -%}
import { describe, it, expect } from "vitest";
import { app } from "../src/api/router.js";

describe("API 路由", () => {
  describe("GET /api/v1/health", () => {
    it("应返回健康状态", async () => {
      const res = app.request("/api/v1/health");
      const json = (await res).json();
      expect(json).toEqual({
        code: 0,
        data: null,
        message: "ok",
      });
    });
  });
});
{%- endif %}
