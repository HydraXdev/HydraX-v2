"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { MissionBrief } from "@/components/bitten/MissionBrief";
import { useTopic, eventBus } from "@/lib/eventBus/realAdapter";
import { startMockEvents } from "@/lib/eventBus/mockSource";
import { executeFire } from "@/lib/api/fireApi";
import { useHotkeys, COMMON_HOTKEYS } from "@/lib/ui/hotkeys";
import { announce } from "@/lib/ui/a11y";
import io from "socket.io-client";

/**
 * Mission Brief Page
 *
 * Composes MissionBrief component with event bus integration
 * Uses mock data in dev mode (NEXT_PUBLIC_USE_MOCKS=1)
 * Auto-redirects to /status after execute
 *
 * Mission Session Token Integration:
 * - Extracts 'token' and 'ms' from URL parameters
 * - Validates token and session state
 * - Connects to Socket.IO with token authentication
 * - Subscribes to real-time mission/trade updates
 */
function MissionPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Extract URL parameters for token-based missions
  const token = searchParams?.get("token") || null;
  const missionSessionId = searchParams?.get("ms") || null;

  // Mission data state - render immediately when loaded
  const [missionAlert, setMissionAlert] = useState<any>(null);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Token validation states
  const [tokenValid, setTokenValid] = useState<boolean>(true);
  const [sessionExpired, setSessionExpired] = useState<boolean>(false);
  const [alreadyExecuted, setAlreadyExecuted] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Execute token state (View vs Execute split)
  const [executeToken, setExecuteToken] = useState<string | null>(null);
  const [tokenExp, setTokenExp] = useState<number | null>(null);
  const [tokenExpired, setTokenExpired] = useState<boolean>(false);
  const [isAuthorizing, setIsAuthorizing] = useState<boolean>(false);
  const [isFiring, setIsFiring] = useState<boolean>(false);

  // Start mock events if in dev mode
  useEffect(() => {
    if (process.env.NEXT_PUBLIC_USE_MOCKS === "1") {
      console.log("[Mission Page] Starting mock events");
      const cleanup = startMockEvents(eventBus.emit);
      return cleanup;
    }
  }, []);

  // Check token expiry (15s skew)
  useEffect(() => {
    if (!tokenExp) return;

    const checkExpiry = () => {
      const now = Math.floor(Date.now() / 1000);
      const skew = 15;
      if (now + skew >= tokenExp) {
        setTokenExpired(true);
        setExecuteToken(null);
      }
    };

    checkExpiry();
    const interval = setInterval(checkExpiry, 5000);
    return () => clearInterval(interval);
  }, [tokenExp]);

  // Fetch latest mission when no session ID provided
  async function fetchLatestMission() {
    try {
      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://134.199.204.67:8888";
      const response = await fetch(`${apiUrl}/api/missions`);
      const data = await response.json();

      if (data.missions && data.missions.length > 0) {
        // Get the most recent mission
        const latestMission = data.missions[0];

        // Fetch full mission details
        const missionResponse = await fetch(
          `${apiUrl}/api/mission/${latestMission.signal_id}`,
        );
        const missionData = await missionResponse.json();

        if (missionData.success && missionData.mission) {
          const mission = missionData.mission;

          // Calculate actual SL/TP from pips if not provided
          const entry = mission.entry_price || 0;
          const stopPips = mission.stop_pips || 20;
          const targetPips = mission.target_pips || 30;

          // Calculate pip size based on symbol
          const symbol = mission.symbol || "";
          let pipSize = 0.0001;
          if (symbol.includes("JPY")) pipSize = 0.01;
          else if (symbol.includes("XAU") || symbol.includes("GOLD"))
            pipSize = 0.1;
          else if (symbol.includes("XAG") || symbol.includes("SILVER"))
            pipSize = 0.001;

          // Calculate actual SL/TP prices from pips
          const sl =
            mission.stop_loss ||
            entry - stopPips * pipSize * (mission.direction === "BUY" ? 1 : -1);
          const tp =
            mission.take_profit ||
            entry +
              targetPips * pipSize * (mission.direction === "BUY" ? 1 : -1);

          // Use provided pips or calculate from prices
          const slPips = stopPips;
          const tpPips = targetPips;
          const riskReward = mission.risk_reward || tpPips / slPips || 1.5;

          // Transform mission data to alert format
          const alert = {
            signalId: mission.signal_id || mission.mission_id,
            patternId: mission.signal_id || mission.mission_id,
            pair: symbol,
            symbol: symbol,
            direction: mission.direction,
            entry: entry,
            stopLoss: sl,
            takeProfit: tp,
            confidence: mission.confidence || mission.tcs_score || 75,
            pattern:
              mission.pattern_type || mission.pattern || "TACTICAL STRIKE",
            patternType:
              mission.pattern_type || mission.pattern || "TACTICAL STRIKE",
            timeframe: mission.timeframe || "M5",
            session: mission.session || "LONDON",
            timestamp:
              typeof mission.created_at === "string"
                ? mission.created_at
                : new Date(
                    (mission.created_timestamp || Date.now() / 1000) * 1000,
                  ).toISOString(),
            riskReward: riskReward,
            pips: { sl: Math.round(slPips), tp: Math.round(tpPips) },
          };

          // Get real user profile
          const profileResponse = await fetch(`${apiUrl}/api/user/profile`);
          const profileData = await profileResponse.json();

          const riskPerTrade = profileData.risk_per_trade || 150;
          const potentialReward = riskPerTrade * riskReward;

          // Create user profile with real data
          const profile = {
            userId: profileData.user_id || "7176191872",
            balance: profileData.balance || 10000,
            activeTrades: profileData.active_trades || 0,
            maxTrades: profileData.max_slots || 3,
            riskPerTrade: riskPerTrade,
            potentialReward: potentialReward,
          };

          // Set data immediately - triggers render
          setMissionAlert(alert);
          setUserProfile(profile);
        }
      } else {
        setErrorMessage("No active missions available");
      }
    } catch (err) {
      console.error("[Mission] Failed to fetch latest mission:", err);
      setErrorMessage("Failed to load mission data");
    } finally {
      setLoading(false);
    }
  }

  // Fetch mission session data IMMEDIATELY and render
  useEffect(() => {
    if (!missionSessionId) {
      // If no mission session, redirect to missions list or fetch latest mission
      fetchLatestMission();
      return;
    }

    async function fetchMissionSession() {
      try {
        // Fetch mission session data from API (use public IP for external access)
        const apiUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://134.199.204.67:8888";
        console.log("[Mission] Fetching session:", missionSessionId);

        const response = await fetch(
          `${apiUrl}/api/mission_session/${missionSessionId}`,
        );
        const data = await response.json();

        console.log("[Mission] Session data:", data);

        if (data.success && data.mission) {
          const mission = data.mission;

          // Use backend-calculated prices (already in correct format)
          const entry = parseFloat(mission.entry_price) || 0;
          const sl = parseFloat(mission.sl) || 0;
          const tp = parseFloat(mission.tp) || 0;
          const stopPips = parseFloat(mission.stop_pips) || 20;
          const targetPips = parseFloat(mission.target_pips) || 30;

          const symbol = mission.symbol || "";
          const riskReward = targetPips / stopPips || 1.5;

          // Get REAL user account data from backend
          const userAccount = data.user_account || {};
          const realBalance = parseFloat(userAccount.balance) || 10000;
          const realEquity = parseFloat(userAccount.equity) || realBalance;
          const realActiveTrades = parseInt(userAccount.active_trades) || 0;
          const maxTrades = parseInt(userAccount.max_trades) || 3;

          // Get fire packet for trade data
          const firePacket = mission.fire_packet || {};
          const lotSize = parseFloat(firePacket.lot) || 0.01;

          // Calculate REAL risk from lot size and SL pips
          const pipValue = 10.0; // $10 per standard lot per pip
          const riskPerTrade = lotSize * stopPips * pipValue;
          const potentialReward = riskPerTrade * riskReward;

          console.log("[Mission] User account:", userAccount);
          console.log("[Mission] Real balance:", realBalance);
          console.log("[Mission] Fire packet:", firePacket);
          console.log("[Mission] Risk calculation:", {
            lotSize,
            stopPips,
            pipValue,
            riskPerTrade,
            potentialReward,
          });

          // Transform mission data to alert format with real data
          const alert = {
            signalId: mission.signal_id,
            patternId: mission.signal_id,
            pair: symbol,
            symbol: symbol,
            direction: mission.direction,
            entry: entry,
            stopLoss: sl,
            takeProfit: tp,
            confidence: parseFloat(mission.confidence) || 75,
            pattern: mission.pattern_type || "UNKNOWN",
            patternType: mission.pattern_type || "UNKNOWN",
            timeframe: mission.timeframe || "M5",
            session: mission.session || "LONDON",
            timestamp: new Date(
              mission.created_at * 1000 || Date.now(),
            ).toISOString(),
            canFire: mission.can_fire,
            briefing: mission.briefing,
            status: mission.status,
            riskReward: riskReward,
            pips: { sl: Math.round(stopPips), tp: Math.round(targetPips) },
          };

          // Create user profile with REAL data from database
          const profile = {
            userId: data.mission_session.user_id || "7176191872",
            level: 25,
            callsign: userAccount.tier || "COMMANDER",
            balance: realBalance,
            riskPerTrade: riskPerTrade,
            potentialReward: potentialReward,
            activeTrades: realActiveTrades,
            maxTrades: maxTrades,
          };

          console.log("[Mission] Final profile:", profile);
          console.log("[Mission] Final alert:", alert);

          // Set data immediately - triggers render
          setMissionAlert(alert);
          setUserProfile(profile);
          setLoading(false);
        } else if (data.error_code === "SESSION_NOT_FOUND") {
          setErrorMessage("Mission session not found");
          setTokenValid(false);
          setLoading(false);
        } else if (data.error_code === "SESSION_EXPIRED") {
          setSessionExpired(true);
          setLoading(false);
        } else {
          setErrorMessage(data.error || "Failed to load mission data");
          setLoading(false);
        }
      } catch (err) {
        console.error("[Mission] Failed to fetch session:", err);
        setErrorMessage("Failed to load mission data");
        setLoading(false);
      }
    }

    fetchMissionSession();
  }, [missionSessionId]);

  // Socket.IO connection with token authentication
  useEffect(() => {
    if (!token || !missionAlert) return;

    const socketUrl =
      process.env.NEXT_PUBLIC_SOCKET_URL || "http://134.199.204.67:8888";
    const socket = io(socketUrl, {
      query: { t: token },
      transports: ["websocket", "polling"],
    });

    // Authentication success
    socket.on("authenticated", () => {
      console.log("[Mission] Socket authenticated");

      // Subscribe to mission-specific topics
      socket.emit("subscribe", {
        topics: [
          "user.profile",
          `mission.alert/${missionAlert.signalId || missionAlert.patternId}`,
          "trades.open",
          "trades.delta",
          "system.status",
        ],
      });
    });

    // Authentication failure
    socket.on("auth_error", (error: any) => {
      console.error("[Mission] Auth error:", error);
      setTokenValid(false);
      setErrorMessage(error.message || "Invalid or expired token");
    });

    // Mission alert updates
    socket.on("mission.alert", (data: any) => {
      console.log("[Mission] Alert update:", data);
      eventBus.emit("mission.alert", data);
    });

    // Trade arming indicator
    socket.on("trades.delta", (data: any) => {
      if (data.status === "ARMING") {
        announce("Trade arming in progress", "polite");
        console.log("[Mission] Trade arming:", data);
      } else if (data.status === "FILLED") {
        announce("Trade filled, redirecting to status", "polite");
        router.push("/status");
      }
    });

    // System status updates (beacons)
    socket.on("system.status", (data: any) => {
      console.log("[Mission] System status:", data);
      // Update operational beacons if needed
    });

    return () => {
      socket.disconnect();
    };
  }, [token, missionAlert, router]);

  // Hotkeys
  useHotkeys({
    [COMMON_HOTKEYS.EXECUTE]: handleExecute,
    [COMMON_HOTKEYS.STATUS]: () => router.push("/status"),
    [COMMON_HOTKEYS.NOTEBOOK]: () => router.push("/notebook"),
    [COMMON_HOTKEYS.HELP]: handleOpenHelp,
  });

  // Handlers
  async function handleExecute() {
    if (!missionAlert || !userProfile) return;

    // TWO-STEP FLOW: Authorize → Fire

    // STEP 1: Get fresh execute token (if needed or expired)
    if (!executeToken || tokenExpired) {
      await authorizeExecution();
      if (!executeToken) return; // Authorization failed
    }

    // STEP 2: Execute trade with token
    await fireWithToken();
  }

  async function authorizeExecution() {
    if (isAuthorizing) return;
    setIsAuthorizing(true);
    setErrorMessage(null);

    try {
      announce("Authorizing execution", "polite");
      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://134.199.204.67:8888";

      const body: any = {};
      if (missionSessionId) body.missionSessionId = missionSessionId;
      if (missionAlert?.signalId) body.alertId = missionAlert.signalId;

      const response = await fetch(`${apiUrl}/mission/authorize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const result = await response.json();

      if (response.status === 409) {
        setAlreadyExecuted(true);
        announce("Mission already executed", "assertive");
        setIsAuthorizing(false);
        return;
      } else if (response.status === 410) {
        setSessionExpired(true);
        announce("Alert expired (8h lifetime)", "assertive");
        setIsAuthorizing(false);
        return;
      } else if (!response.ok) {
        setErrorMessage(result.error || "Authorization failed");
        announce(`Authorization failed: ${result.error}`, "assertive");
        setIsAuthorizing(false);
        return;
      }

      // Store execute token
      setExecuteToken(result.executeToken);
      setTokenExp(result.exp);
      setTokenExpired(false);
      announce("Execution authorized", "polite");
      console.log("[Mission] Execute token obtained, exp:", result.exp);
    } catch (error) {
      setErrorMessage("Authorization request failed");
      announce("Authorization failed", "assertive");
      console.error("[Mission] Authorize error:", error);
    } finally {
      setIsAuthorizing(false);
    }
  }

  async function fireWithToken() {
    if (isFiring || !executeToken) return;
    setIsFiring(true);
    setErrorMessage(null);

    try {
      announce("Executing trade", "polite");
      const clientRequestId = crypto.randomUUID();

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        Authorization: `Bearer ${executeToken}`,
      };

      const body: any = {
        clientRequestId,
        alertId: missionAlert.signalId || missionAlert.patternId,
        entry: missionAlert.entry,
        stopLoss: missionAlert.stopLoss,
        takeProfit: missionAlert.takeProfit,
        riskUsd: userProfile.riskPerTrade,
        missionSessionId,
      };

      const response = await fetch("/api/fire", {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });

      const result = await response.json();

      // Handle HTTP status codes
      if (response.status === 409) {
        setAlreadyExecuted(true);
        announce("This order has already been executed", "assertive");
        setIsFiring(false);
        return;
      } else if (response.status === 410) {
        setSessionExpired(true);
        announce("Mission session has expired", "assertive");
        setIsFiring(false);
        return;
      } else if (response.status === 422) {
        setErrorMessage(result.error || "Risk validation failed");
        announce(`Trade rejected: ${result.error}`, "assertive");
        setIsFiring(false);
        return;
      } else if (response.status === 401 || response.status === 403) {
        // Token expired or invalid - mark for refresh
        setTokenExpired(true);
        setExecuteToken(null);
        setErrorMessage("Execute token expired - please authorize again");
        announce("Token expired - authorization required", "assertive");
        setIsFiring(false);
        return;
      } else if (response.status === 202) {
        announce("Trade submitted, awaiting confirmation", "polite");
        console.log("[Mission] Trade pending:", result.opId);
        // Continue to redirect
      } else if (!result.success) {
        setErrorMessage(result.error || "Trade failed");
        announce(`Trade failed: ${result.error}`, "assertive");
        setIsFiring(false);
        return;
      }

      // Auto-redirect to in-progress monitor
      router.push("/in-progress");
    } catch (error) {
      setErrorMessage("Trade execution failed");
      announce("Trade execution failed", "assertive");
      console.error("[Mission] Fire error:", error);
      setIsFiring(false);
    }
  }

  function handleGotoStatus() {
    router.push("/status");
  }

  function handleOpenNotebook() {
    router.push("/notebook");
  }

  function handleOpenMenu() {
    // TODO: Open menu drawer/modal
    console.log("[Mission] Open menu");
  }

  function handleOpenHelp() {
    // TODO: Open help modal
    console.log("[Mission] Open help");
  }

  // Error states for token-based missions
  if (sessionExpired) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="text-center max-w-md px-4">
          <div className="text-6xl mb-4">⏱️</div>
          <h2 className="text-2xl font-bold text-[#f56565] mb-2">
            Mission Session Expired
          </h2>
          <p className="text-[#cbd5e0] mb-6">
            This mission link has expired. Please request a new mission link to
            continue.
          </p>
          <button
            onClick={() => router.push("/")}
            className="px-6 py-3 bg-[#34d399] text-[#0a0e1a] font-bold rounded-lg hover:bg-[#2c9a7a] transition-colors"
          >
            Request New Link
          </button>
        </div>
      </div>
    );
  }

  if (alreadyExecuted) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="text-center max-w-md px-4">
          <div className="text-6xl mb-4">✅</div>
          <h2 className="text-2xl font-bold text-[#fbbf24] mb-2">
            Order Already Executed
          </h2>
          <p className="text-[#cbd5e0] mb-6">
            This mission has already been executed. Check your status board for
            details.
          </p>
          <button
            onClick={() => router.push("/status")}
            className="px-6 py-3 bg-[#34d399] text-[#0a0e1a] font-bold rounded-lg hover:bg-[#2c9a7a] transition-colors"
          >
            View Status Board
          </button>
        </div>
      </div>
    );
  }

  if (!tokenValid && errorMessage) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="text-center max-w-md px-4">
          <div className="text-6xl mb-4">🚫</div>
          <h2 className="text-2xl font-bold text-[#f56565] mb-2">
            Access Denied
          </h2>
          <p className="text-[#cbd5e0] mb-6">{errorMessage}</p>
          <button
            onClick={() => router.push("/")}
            className="px-6 py-3 bg-[#34d399] text-[#0a0e1a] font-bold rounded-lg hover:bg-[#2c9a7a] transition-colors"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="text-center max-w-md px-4">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-[#fbbf24] mb-2">
            {tokenExpired ? "Execute Token Expired" : "Trade Validation Error"}
          </h2>
          <p className="text-[#cbd5e0] mb-6">{errorMessage}</p>
          {tokenExpired ? (
            <button
              onClick={() => {
                setErrorMessage(null);
                setTokenExpired(false);
                authorizeExecution();
              }}
              disabled={isAuthorizing}
              className="px-6 py-3 bg-[#34d399] text-[#0a0e1a] font-bold rounded-lg hover:bg-[#2c9a7a] transition-colors disabled:opacity-50"
            >
              {isAuthorizing ? "Authorizing..." : "Get New Execute Token"}
            </button>
          ) : (
            <button
              onClick={() => setErrorMessage(null)}
              className="px-6 py-3 bg-[#34d399] text-[#0a0e1a] font-bold rounded-lg hover:bg-[#2c9a7a] transition-colors"
            >
              Return to Mission
            </button>
          )}
        </div>
      </div>
    );
  }

  // Loading state
  if (!userProfile || !missionAlert) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="text-center">
          <div
            className="w-12 h-12 border-4 border-[#34d399] border-t-transparent rounded-full animate-spin mx-auto mb-4"
            aria-label="Loading"
          />
          <p className="text-[#cbd5e0]">Loading mission brief...</p>
        </div>
      </div>
    );
  }

  // Transform data to TradeAlertView format
  const tradeAlertUserData = {
    balance: 10005.0, // TODO: Get from user profile
    activeTrades: userProfile?.capacity?.used || 2,
    maxTrades: userProfile?.capacity?.total || 6,
    riskPerTrade: userProfile?.riskPerTrade || 100.0,
    potentialReward:
      (userProfile?.riskPerTrade || 100) * (missionAlert?.riskReward || 1.5),
  };

  const tradeAlertData = {
    pattern: missionAlert.pattern?.replace(/_/g, " ") || "UNKNOWN",
    patternId: 1,
    pair: missionAlert.pair || missionAlert.symbol,
    timeframe: missionAlert.timeframe || "5-MIN",
    session: missionAlert.session || "LONDON SESSION",
    timestamp: new Date().toISOString(),
    confidence: missionAlert.confidence || 85,
    entry: missionAlert.entry || 0,
    takeProfit: missionAlert.takeProfit || 0,
    stopLoss: missionAlert.stopLoss || 0,
    pips: missionAlert.pips || { tp: 14.8, sl: 10.0 },
    riskReward: missionAlert.riskReward || 1.5,
  };

  return (
    <MissionBrief
      userData={tradeAlertUserData}
      alertData={tradeAlertData}
      onExecute={handleExecute}
      executing={isFiring}
      onGoToDashboard={() => router.push("/status")}
      onOpenNotebook={() => router.push("/notebook")}
    />
  );
}

export default function MissionPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
          <div className="text-center">
            <div
              className="w-12 h-12 border-4 border-[#34d399] border-t-transparent rounded-full animate-spin mx-auto mb-4"
              aria-label="Loading"
            />
            <p className="text-[#cbd5e0]">Loading mission brief...</p>
          </div>
        </div>
      }
    >
      <MissionPageContent />
    </Suspense>
  );
}
