import ws from "k6/ws";
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 20,
  duration: "60s",
  thresholds: {
    http_req_duration: ["p(95)<250"],
    ws_connecting: ["p(95)<1000"],
    ws_msgs_received: ["rate>10"],
    checks: ["rate>0.9"],
  },
};

const API = __ENV.API || "http://localhost:8888";
const KEY = __ENV.KEY || "test-key";

export default function () {
  const wsUrl = `ws://localhost:8888/socket.io/?account_id=TEST&token=${KEY}&types=events,account,heartbeat&symbol=EURUSD,GBPUSD`;
  const params = {
    headers: { "X-API-Key": KEY },
  };

  // WebSocket load test
  const res = ws.connect(wsUrl, params, function (socket) {
    socket.setTimeout(function () {
      socket.ping();
    }, 5000);

    socket.on("open", function () {
      socket.send(
        JSON.stringify({
          type: "subscribe",
          topic: "events",
          account_id: "TEST",
        }),
      );
    });

    let messageCount = 0;
    socket.on("message", function (msg) {
      messageCount++;
      // Track message processing - just count for load testing
    });

    socket.on("error", function (e) {
      console.log("WebSocket error:", e);
    });

    // Generate API load while WebSocket is connected
    for (let i = 0; i < 10; i++) {
      const tradeRequest = {
        idempotency_key: `load-test-${__VU}-${Date.now()}-${i}`,
        account_id: "TEST",
        symbol: "EURUSD",
        side: "buy",
        volume: 0.01,
        meta: { test: true },
      };

      const apiRes = http.post(
        `${API}/v1/trades/open`,
        JSON.stringify(tradeRequest),
        {
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": KEY,
          },
        },
      );

      check(apiRes, {
        "API status is 200 or 403": (r) => [200, 403].includes(r.status),
        "API response time < 250ms": (r) => r.timings.duration < 250,
      });

      sleep(0.1); // 10 requests per second per VU
    }

    // Keep WebSocket open for remainder of test
    sleep(1);
  });

  check(res, {
    "WebSocket status is 101": (r) => r && r.status === 101,
  });
}
