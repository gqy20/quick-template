/**
 * {{ project_name }}
 * {{ description }}
 */

export { greet } from "./core.js";
export { logger } from "./logger.js";
{% if add_api -%}
export { app } from "./api/router.js";
{%- endif %}
