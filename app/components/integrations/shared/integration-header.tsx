'use client'

import { ReactNode } from 'react'

interface IntegrationHeaderProps {
  title: string
  description?: string
  icon?: ReactNode
}

export function IntegrationHeader({ title, description, icon }: IntegrationHeaderProps) {
  return (
    <div className="flex items-center space-x-4 mb-6">
      {icon && <div className="w-10 h-10 flex items-center justify-center">{icon}</div>}
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        {description && <p className="text-muted-foreground mt-1">{description}</p>}
      </div>
    </div>
  )
}
