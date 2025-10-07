module.exports = {
  apps: [
    {
      name: "bitten-ui",
      cwd: "/root/HydraX-v2/bitten-ui",
      script: "node_modules/.bin/next",
      args: "start -p 3000",
      env: {
        NODE_ENV: "production",
        NEXT_PUBLIC_BASE_URL: "https://www.joinBITTEN.com",
        NEXT_PUBLIC_API_URL: "https://www.joinBITTEN.com",
        NEXT_PUBLIC_SOCKET_URL: "https://www.joinBITTEN.com",
        NEXT_PUBLIC_BUS_URL: "wss://www.joinBITTEN.com/ws/ui",
        NEXT_PUBLIC_API_FIRE: "https://www.joinBITTEN.com/api/fire",
        NEXT_PUBLIC_API_CLOSE_ALL:
          "https://www.joinBITTEN.com/api/trades/close-all",
        NEXT_PUBLIC_USE_MOCKS: "0",
      },
    },
  ],
};
