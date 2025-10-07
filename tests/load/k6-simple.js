import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 10,
  duration: "30s",
  thresholds: {
    http_req_duration: ["p(95)<250"],
    checks: ["rate>0.9"],
  },
};

const API = "http://localhost:8888";

export default function () {
  // Test health endpoint
  const healthRes = http.get(`${API}/healthz`);
  check(healthRes, {
    "health status is 200": (r) => r.status === 200,
    "health response time < 100ms": (r) => r.timings.duration < 100,
  });

  // Test API health endpoint
  const apiHealthRes = http.get(`${API}/api/health`);
  check(apiHealthRes, {
    "api health status is 200": (r) => r.status === 200,
    "api health has schema hash": (r) => r.json().schema_sha256 !== undefined,
  });

  // Test docs endpoint
  const docsRes = http.get(`${API}/docs`);
  check(docsRes, {
    "docs status is 200": (r) => r.status === 200,
    "docs contains swagger": (r) => r.body.includes("swagger"),
  });

  // Test API endpoint (expect error but fast response)
  const tradeRes = http.post(
    `${API}/v1/trades/open`,
    JSON.stringify({
      account_id: "TEST",
      symbol: "EURUSD",
      side: "buy",
      volume: 0.01,
    }),
    {
      headers: { "Content-Type": "application/json" },
    },
  );

  check(tradeRes, {
    "trade endpoint responsive": (r) => r.status >= 400 && r.status < 500,
    "trade response time < 250ms": (r) => r.timings.duration < 250,
  });

  sleep(0.1);
}
