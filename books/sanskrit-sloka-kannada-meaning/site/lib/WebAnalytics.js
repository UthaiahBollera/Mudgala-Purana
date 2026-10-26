'use client';
import { Analytics } from '@vercel/analytics/next';
import { pageviewOnly } from './analytics-policy.mjs';

export default function WebAnalytics() {
  return <Analytics beforeSend={pageviewOnly} />;
}
