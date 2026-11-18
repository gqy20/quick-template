{{#if add_api}}
export { app } from "./api/router.js";
{{#endif}}
export { greet } from "./core.js";
export { logger } from "./logger.js";
