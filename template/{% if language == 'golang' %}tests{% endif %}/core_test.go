package tests

import (
	"testing"

	"{% if repository_provider == 'https://github.com' %}github.com/{{ repository_username }}/{{ project_slug }}{% else %}{{ repository_provider }}/{{ repository_username }}/{{ project_slug }}{% endif %}/internal/service"
)

func TestGreet(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{"默认名称", "", "你好，世界！"},
		{"指定名称", "Go", "你好，Go！"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := service.Greet(tt.input)
			if result != tt.expected {
				t.Errorf("Greet(%q) = %q, want %q", tt.input, result, tt.expected)
			}
		})
	}
}
