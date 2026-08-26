import './globals.css';
import StudentPwaRegister from './components/StudentPwaRegister';

export const metadata = {
  title: 'LAFRE',
  applicationName: 'LAFRE Student',
  description: 'A focused legal study workspace for law students.',
  manifest: '/manifest.json',
  icons: {
    icon: [
      { url: '/icons/lafre-student-icon-192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icons/lafre-student-icon-512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [{ url: '/icons/lafre-student-icon-192.png', sizes: '192x192', type: 'image/png' }],
  },
  appleWebApp: {
    capable: true,
    title: 'LAFRE Student',
    statusBarStyle: 'black-translucent',
  },
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#0f1b2d',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <StudentPwaRegister />
        {children}
      </body>
    </html>
  );
}
