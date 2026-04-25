// Package service 提供业务逻辑
package service

import "fmt"

// Greet 返回问候语
func Greet(name string) string {
	if name == "" {
		name = "世界"
	}
	return fmt.Sprintf("你好，%s！", name)
}
