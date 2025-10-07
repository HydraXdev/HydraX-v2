#!/usr/bin/env node

// Test real backend integration
import fetch from "node-fetch";

console.log("\n🎯 BITTEN Backend Integration Test");
console.log("=".repeat(50));

const API_URL = "http://localhost:8888";

async function testBackendConnection() {
  console.log("\n1️⃣ Testing API health...");
  try {
    const response = await fetch(`${API_URL}/api/health`);
    const data = await response.json();
    console.log("✅ Health check:", data);
  } catch (error) {
    console.log("❌ Health check failed:", error.message);
  }

  console.log("\n2️⃣ Fetching signals...");
  try {
    const response = await fetch(`${API_URL}/api/signals`);
    const data = await response.json();
    console.log(`✅ Found ${data.count} signals`);
    console.log("Available modes:", data.available_modes);

    if (data.signals && data.signals.length > 0) {
      console.log("\nFirst signal:");
      const signal = data.signals[0];
      console.log(`  ID: ${signal.signal_id}`);
      console.log(`  Symbol: ${signal.symbol}`);
      console.log(`  Direction: ${signal.direction}`);
      console.log(`  Confidence: ${signal.confidence}%`);
      console.log(`  Mode: ${signal.signal_mode}`);
      console.log(`  Can Fire: ${signal.can_fire}`);
    }
  } catch (error) {
    console.log("❌ Signals fetch failed:", error.message);
  }

  console.log("\n3️⃣ Testing account info...");
  try {
    const response = await fetch(`${API_URL}/api/account`);
    const data = await response.json();
    console.log("✅ Account data:", data);
  } catch (error) {
    console.log("❌ Account fetch failed:", error.message);
  }

  console.log("\n4️⃣ Testing WebSocket endpoint...");
  try {
    // Just check if Socket.IO endpoint responds
    const response = await fetch(
      `${API_URL}/socket.io/?EIO=4&transport=polling`,
    );
    if (response.ok) {
      console.log("✅ Socket.IO endpoint is available");
    } else {
      console.log("⚠️ Socket.IO returned status:", response.status);
    }
  } catch (error) {
    console.log("❌ Socket.IO check failed:", error.message);
  }

  console.log("\n5️⃣ Testing ZMQ ports...");
  const zmqPorts = [5555, 5556, 5557, 5558, 5560];
  for (const port of zmqPorts) {
    try {
      const { exec } = await import("child_process");
      await new Promise((resolve) => {
        exec(`ss -tuln | grep :${port}`, (error, stdout) => {
          if (stdout.includes(`:${port}`)) {
            console.log(`✅ Port ${port}: LISTENING`);
          } else {
            console.log(`❌ Port ${port}: NOT LISTENING`);
          }
          resolve();
        });
      });
    } catch (error) {
      console.log(`❌ Port ${port} check failed`);
    }
  }

  console.log("\n" + "=".repeat(50));
  console.log("🏁 Integration test complete!");
  console.log("\n🔗 Frontend can now connect to:");
  console.log("  - REST API: http://localhost:8888/api/*");
  console.log("  - WebSocket: http://localhost:8888 (Socket.IO)");
  console.log("  - ZMQ feeds: Ports 5555-5560");
  console.log("\n⚠️ Note: Market closed until tomorrow night");
  console.log("  Using cached demo signals for testing");
}

testBackendConnection();
