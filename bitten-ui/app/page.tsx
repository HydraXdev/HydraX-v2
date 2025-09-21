"use client"

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to War Room on landing
    router.push('/war-room')
  }, [router])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-mint mb-2">BITTEN</h1>
        <p className="text-secondary">Loading tactical interface...</p>
      </div>
    </div>
  )
}