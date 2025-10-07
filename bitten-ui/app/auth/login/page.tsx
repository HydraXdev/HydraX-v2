'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

function LoginContent() {
  const searchParams = useSearchParams();
  const error = searchParams.get('error');
  const message = searchParams.get('message');

  const getErrorDetails = () => {
    switch (error) {
      case 'expired':
        return {
          title: '⏰ Session Expired',
          description: message || 'Your session has expired. Please access the page from Telegram again.',
          action: 'Return to Telegram and use the command again.'
        };
      case 'invalid':
        return {
          title: '🔒 Access Denied',
          description: message || 'Invalid access. Please use the links provided in Telegram.',
          action: 'Use /brief, /war, /live, or /notebook commands in the BITTEN bot.'
        };
      default:
        return {
          title: '🎯 BITTEN Access',
          description: 'Secure access to BITTEN trading interface.',
          action: 'Use the official BITTEN Telegram bot to access this page.'
        };
    }
  };

  const { title, description, action } = getErrorDetails();

  return (
    <div className="min-h-screen bg-primary flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="panel-elevated p-8 text-center">
          <div className="mb-6">
            <div className="text-4xl mb-4">🎮</div>
            <h1 className="text-2xl font-tactical text-mint mb-2">{title}</h1>
            <p className="text-secondary mb-6">{description}</p>
          </div>

          <div className="space-y-4">
            <div className="bg-overlay/50 rounded p-4 border border-active/30">
              <p className="text-sm text-tertiary font-code">
                {action}
              </p>
            </div>

            <div className="text-xs text-muted">
              <p>Secure access powered by BITTEN Protocol</p>
              <p className="mt-1">All links expire after 5 minutes for security</p>
            </div>
          </div>

          <div className="mt-8 space-y-2">
            <h3 className="text-sm font-tactical text-cyan">Available Commands:</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-secondary/30 rounded px-2 py-1 font-code">/brief</div>
              <div className="bg-secondary/30 rounded px-2 py-1 font-code">/war</div>
              <div className="bg-secondary/30 rounded px-2 py-1 font-code">/live</div>
              <div className="bg-secondary/30 rounded px-2 py-1 font-code">/notebook</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-primary flex items-center justify-center">
        <div className="text-mint">Loading...</div>
      </div>
    }>
      <LoginContent />
    </Suspense>
  );
}