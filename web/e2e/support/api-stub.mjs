import { createServer } from "node:http";

const port = Number(process.env.TASKPILOT_E2E_API_PORT ?? "7152");

createServer((request, response) => {
  response.setHeader("Content-Type", "application/json");

  if (request.url === "/api/health") {
    response.end(JSON.stringify({ status: "ok" }));
    return;
  }

  if (request.url === "/api/projects") {
    response.end(JSON.stringify([]));
    return;
  }

  response.statusCode = 404;
  response.end(JSON.stringify({ detail: "Not found" }));
}).listen(port, "127.0.0.1");
