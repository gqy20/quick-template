import { describe, it, expect } from "vitest";
import { greet, add } from "../src/core.js";

describe("核心功能", () => {
  describe("greet", () => {
    it("默认名称应返回问候语", () => {
      expect(greet()).toBe("你好，世界！");
    });

    it("指定名称应返回对应问候语", () => {
      expect(greet("TypeScript")).toBe("你好，TypeScript！");
    });
  });

  describe("add", () => {
    it("两数相加", () => {
      expect(add(1, 2)).toBe(3);
    });

    it("负数相加", () => {
      expect(add(-1, 1)).toBe(0);
    });
  });
});
