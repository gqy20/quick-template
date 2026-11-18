module {{ go_module_path }}

go {{ go_version }}

{{#if add_api}}
require (
	github.com/gin-contrib/cors v1.7.10
	github.com/gin-gonic/gin v1.12.0
)
{{#endif}}
