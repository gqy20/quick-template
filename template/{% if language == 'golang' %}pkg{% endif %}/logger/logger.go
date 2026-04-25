// Package logger 提供统一的日志接口
package logger

import (
	"io"
	"log/slog"
	"os"
)

var defaultLogger *slog.Logger

// Init 初始化日志系统
func Init(level slog.Level) {
	opts := &slog.HandlerOptions{
		Level: level,
		AddSource: true,
		ReplaceAttr: func(groups []string, a slog.Attr) slog.Attr {
			// 将时间格式化为更友好的格式
			if a.Key == slog.TimeKey {
				a.Value = slog.StringValue(a.Value.Time().Format("2006-01-02 15:04:05"))
			}
			return a
		},
	}

	handler := slog.NewJSONHandler(os.Stdout, opts)
	defaultLogger = slog.New(handler)

	slog.SetDefault(defaultLogger)
}

// Get 返回默认日志记录器
func Get() *slog.Logger {
	return defaultLogger
}

// WithWriter 创建写入指定 io.Writer 的日志器
func WithWriter(w io.Writer) *slog.Logger {
	handler := slog.NewJSONHandler(w, nil)
	return slog.New(handler)
}
