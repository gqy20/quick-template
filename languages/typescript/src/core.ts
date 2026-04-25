/**
 * 核心功能模块
 */

/** 返回问候语 */
export function greet(name: string = "世界"): string {
  return `你好，${name}！`;
}

/** 两数相加 */
export function add(a: number, b: number): number {
  return a + b;
}
