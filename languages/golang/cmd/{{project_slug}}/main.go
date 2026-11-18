// Command {{ project_slug }} starts the application.
package main

import ({{#if add_api}}
	"log/slog"
	"os"

	"{{ go_module_path }}/internal/handler"
	"{{ go_module_path }}/pkg/logger"{{#else}}
	"fmt"
	"log/slog"

	"{{ go_module_path }}/pkg/logger"{{#endif}}
)

// 版本信息（编译时注入）
var (
	version = "dev"
	commit  = "none"
	date    = "unknown"
)

func main() {
	// 初始化日志
	logger.Init(slog.LevelInfo)

	slog.Info(
		"启动 {{ project_name_escaped }}",
		"version", version,
		"commit", commit,
		"date", date,
	)

{{#if add_api}}	// 启动 API 服务器
	if err := handler.Run(); err != nil {
		slog.Error("服务启动失败", "error", err)
		os.Exit(1)
	}
{{#else}}	// TODO: 添加你的业务逻辑
	fmt.Println("Hello from {{ project_name_escaped }}!")
{{#endif}}}
