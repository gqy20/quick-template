package main

import (
	"fmt"
	"log/slog"
	"os"

	"{% if repository_provider == 'https://github.com' %}github.com/{{ repository_username }}/{{ project_slug }}{% else %}{{ repository_provider }}/{{ repository_username }}/{{ project_slug }}{% endif %}/internal/handler"
	"{% if repository_provider == 'https://github.com' %}github.com/{{ repository_username }}/{{ project_slug }}{% else %}{{ repository_provider }}/{{ repository_username }}/{{ project_slug }}{% endif %}/pkg/logger"
)

// {{ project_name }} 版本信息（编译时注入）
var (
	version = "dev"
	commit  = "none"
	date    = "unknown"
)

func main() {
	// 初始化日志
	logger.Init(slog.LevelInfo)

	slog.Info("启动 {{ project_name }}", "version", version)

	{% if add_api -%}
	// 启动 API 服务器
	if err := handler.Run(); err != nil {
		slog.Error("服务启动失败", "error", err)
		os.Exit(1)
	}
	{%- else -%}
	// TODO: 添加你的业务逻辑
	fmt.Println("Hello from {{ project_name }}!")
	{%- endif %}
}
