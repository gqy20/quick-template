import { serve } from "@hono/node-server";
import { app } from "./api/router.js";

serve(
  { fetch: app.fetch, hostname: "127.0.0.1", port: Number(process.env.PORT ?? 3000) },
  ({ port }) => console.log(`http://127.0.0.1:${port}`),
);
