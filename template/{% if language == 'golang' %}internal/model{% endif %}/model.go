// Package model 定义数据模型
package model

// Response 统一响应格式
type Response struct {
	Code    int         `json:"code"`
	Data    interface{} `json:"data"`
	Message string      `json:"message"`
}

// SuccessResponse 成功响应
func SuccessResponse(data interface{}) Response {
	return Response{
		Code:    0,
		Data:    data,
		Message: "成功",
	}
}

// ErrorResponse 错误响应
func ErrorResponse(code int, msg string) Response {
	return Response{
		Code:    code,
		Data:    nil,
		Message: msg,
	}
}
