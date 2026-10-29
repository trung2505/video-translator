import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Video Translator - Dịch Video Tiếng Trung sang Tiếng Việt',
  description: 'Ứng dụng dịch video tiếng Trung sang tiếng Việt với AI',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="vi">
      <body className="bg-gray-50">{children}</body>
    </html>
  )
}