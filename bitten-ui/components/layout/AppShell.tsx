"use client"

import React, { ReactNode } from 'react'
import { SideNav } from './SideNav'
import { HUDHeader } from './HUDHeader'
import { motion, AnimatePresence } from 'framer-motion'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-[rgb(var(--bg-primary))] flex">
      {/* Side Navigation */}
      <SideNav />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* HUD Header */}
        <HUDHeader />

        {/* Page Content */}
        <main className="flex-1 p-4 md:p-6 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}