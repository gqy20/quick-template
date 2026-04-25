// Package handler 提供 HTTP 处理器
package handler

import (
	"log/slog"
	"net/http"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

// Run 启动 HTTP 服务器
func Run() error {
	r := gin.Default()

	// CORS 中间件
	r.Use(cors.Default())

	// 健康检查
	r.GET("/api/v1/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"code":    0,
			"data":    nil,
			"message": "ok",
		})
	})

	// TODO: 注册更多路由

	slog.Info("HTTP 服务器启动", "addr", ":8080")
	return r.Run(":8080")
}
