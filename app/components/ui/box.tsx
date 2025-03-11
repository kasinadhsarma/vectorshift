import { cn } from "@/lib/utils"
import { type HTMLAttributes, forwardRef } from "react"

export interface BoxProps extends HTMLAttributes<HTMLDivElement> {}

const Box = forwardRef<HTMLDivElement, BoxProps>(({ className, ...props }, ref) => {
  return <div className={cn(className)} ref={ref} {...props} />
})

Box.displayName = "Box"

export { Box }

