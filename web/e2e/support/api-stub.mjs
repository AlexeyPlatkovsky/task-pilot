import { createServer } from "node:http";

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
}).listen(7152, "127.0.0.1");
