// Patch for BITTENBridge_TradeExecutor_ZMQ_v7.mq5
// Add this OnTick() implementation to stream tick data

void OnTick()
{
   // Only send tick data if we're connected
   if(!g_zmq_connected) return;
   
   // Get current tick data
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double spread = (ask - bid) / _Point;
   long volume = SymbolInfoInteger(_Symbol, SYMBOL_VOLUME);
   
   // Format tick data as JSON
   string tick = StringFormat(
      "{\"type\":\"tick\",\"symbol\":\"%s\",\"bid\":%.5f,\"ask\":%.5f,\"spread\":%.1f,\"volume\":%d,\"timestamp\":%d}",
      _Symbol, bid, ask, spread, volume, TimeCurrent()
   );
   
   // Send via heartbeat socket (PUSH to port 5556)
   uchar buffer[];
   StringToCharArray(tick, buffer);
   ArrayResize(buffer, ArraySize(buffer) - 1);  // Remove null terminator
   
   int result = zmq_send(g_zmq_heartbeat_socket, buffer, ArraySize(buffer), 0);
   
   // Optional: Log first few ticks for debugging
   static int tick_count = 0;
   if(result >= 0 && tick_count < 5)
   {
      tick_count++;
      Print("📊 Sent tick #", tick_count, ": ", tick);
   }
}