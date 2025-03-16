"use client"

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="p-6">
      {children}
    </div>
  )
}
