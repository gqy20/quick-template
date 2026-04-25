package tests

import (
	"net/http"
	"net/http/httptest"
	"testing"

	{% if add_api -%}
	"github.com/gin-gonic/gin"
	{%- endif %}
)

{% if add_api -%}
func TestHealthCheck(t *testing.T) {
	gin.SetMode(gin.TestMode)
	r := gin.Default()
	r.GET("/api/v1/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"code":    0,
			"data":    nil,
			"message": "ok",
		})
	})

	req := httptest.NewRequest(http.MethodGet, "/api/v1/health", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", w.Code)
	}
}
{%- endif %}
