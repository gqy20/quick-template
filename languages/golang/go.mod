module {{#if repository_provider=='https://github.com'}}github.com/{{repository_username}}/{{project_slug}}{{#else}}{{repository_provider}}/{{repository_username}}/{{project_slug}}{{#endif}}

go {{ go_version }}

{{#if add_api}}
require (
	github.com/gin-contrib/cors v1.7.10
	github.com/gin-gonic/gin v1.12.0
)
{{#endif}}
