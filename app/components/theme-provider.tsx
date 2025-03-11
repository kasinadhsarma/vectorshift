r"use client"

import * as React from "react"
import { ThemeProvider as NextThemesProvider } from "next-themes"
import { type ThemeProviderProps } from "next-themes/dist/types"
import { GoogleAuthProvider } from "@/components/auth/google-auth-provider"

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return (
    <NextThemesProvider {...props}>
      <GoogleAuthProvider>
        {children}
      </GoogleAuthProvider>
    </NextThemesProvider>
  )
}
