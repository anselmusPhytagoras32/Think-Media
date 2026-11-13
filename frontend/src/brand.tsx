// FR01–11 / NFR05/09: original, consistent brand and navigation marks.
import type { ReactNode } from "react";

export type IconName =
  | "home"
  | "learning"
  | "opportunities"
  | "applications"
  | "suggestions"
  | "guidance"
  | "verification"
  | "content"
  | "reports"
  | "audit"
  | "profile"
  | "organization"
  | "applicants"
  | "listing-board";

type MarkProps = { size?: number; className?: string };

export function BrandMark({ size = 36, className = "" }: MarkProps) {
  return (
    <svg
      viewBox="0 0 40 40"
      width={size}
      height={size}
      className={`brand-mark ${className}`.trim()}
      aria-hidden="true"
      focusable="false"
      fill="none"
    >
      <rect x="1" y="1" width="38" height="38" rx="13" fill="currentColor" />
      <path
        d="M10 13.5c4.1-.9 7.1.1 10 2.2 2.9-2.1 5.9-3.1 10-2.2v14c-4.1-.9-7.1.1-10 2.2-2.9-2.1-5.9-3.1-10-2.2v-14Z"
        fill="#FFFFFF"
      />
      <path
        d="M20 16v13"
        stroke="#402C75"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <path
        d="M24.5 8.3c-.3 3.7-2.3 6-5.8 7.1-.2-3.7 1.8-6.2 5.8-7.1Z"
        fill="#72C7D0"
      />
      <circle cx="29.3" cy="9.8" r="2.8" fill="#ED4D6E" />
    </svg>
  );
}

const marks: Record<IconName, ReactNode> = {
  organization: (
    <>
      <path
        d="M5 28V10l11-6 11 6v18H5Z"
        fill="currentColor"
        fillOpacity=".08"
      />
      <path d="M5 28V10l11-6 11 6v18M3 28h26M11 14h2M19 14h2M11 19h2M19 19h2M13 28v-5h6v5" />
      <path
        d="m12 10 4-2 4 2"
        stroke="var(--icon-accent, #72C7D0)"
        strokeWidth="3"
      />
    </>
  ),
  applicants: (
    <>
      <rect
        x="3"
        y="6"
        width="23"
        height="23"
        rx="4"
        fill="currentColor"
        fillOpacity=".08"
      />
      <rect x="3" y="6" width="23" height="23" rx="4" />
      <path d="M10 6V3h9v3M8 23v-1a5 5 0 0 1 10 0v1M8 24h10M21 14h2M21 19h2" />
      <circle cx="13" cy="13" r="3" fill="var(--icon-accent, #D7A3B7)" />
      <circle cx="26" cy="25" r="5" fill="var(--icon-accent, #72C7D0)" />
      <path d="m23.7 25 1.6 1.6 2.8-3" />
    </>
  ),
  "listing-board": (
    <>
      <rect
        x="4"
        y="5"
        width="24"
        height="22"
        rx="4"
        fill="currentColor"
        fillOpacity=".08"
      />
      <rect x="4" y="5" width="24" height="22" rx="4" />
      <path d="M4 11h24M11 11v16M16 16h7M16 21h5" />
      <path
        d="M7 15h1v3H7zM7 21h1v2H7z"
        stroke="var(--icon-accent, #D8789E)"
        strokeWidth="2.5"
      />
    </>
  ),
  home: (
    <>
      <path
        d="m5 14 11-9 11 9v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V14Z"
        fill="currentColor"
        fillOpacity=".1"
      />
      <path d="m3.5 15 11-9.1a2.4 2.4 0 0 1 3 0l11 9.1M6 13.4V26a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V13.4M12.5 28v-9h7v9" />
      <path d="M21.7 7.9V4.5h4V11" />
      <path
        d="M14 23h4v5h-4z"
        fill="var(--icon-accent, #D8789E)"
        stroke="none"
      />
    </>
  ),
  learning: (
    <>
      <path
        d="M4 7c4-1.1 8-.3 12 2 4-2.3 8-3.1 12-2v19c-4-1.1-8-.3-12 2-4-2.3-8-3.1-12-2V7Z"
        fill="currentColor"
        fillOpacity=".1"
      />
      <path d="M4 7c4-1.1 8-.3 12 2 4-2.3 8-3.1 12-2v19c-4-1.1-8-.3-12 2-4-2.3-8-3.1-12-2V7ZM16 9v19M8 12h4M8 16h4M20 16h4M20 20h4" />
      <path
        d="M21 6v7l2.3-1.5L26 13V5.7"
        fill="var(--icon-accent, #72C7D0)"
        stroke="none"
      />
    </>
  ),
  opportunities: (
    <>
      <rect
        x="4"
        y="10"
        width="24"
        height="18"
        rx="4"
        fill="currentColor"
        fillOpacity=".1"
      />
      <rect x="4" y="10" width="24" height="18" rx="4" />
      <path d="M11 10V7a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v3M4 17a26 26 0 0 0 24 0" />
      <rect
        x="13"
        y="16"
        width="6"
        height="6"
        rx="1.5"
        fill="var(--icon-accent, #E0B0A4)"
      />
    </>
  ),
  applications: (
    <>
      <path
        d="M8 6h13l5 5v16a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2Z"
        fill="currentColor"
        fillOpacity=".1"
      />
      <path d="M8 6h13l5 5v16a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2ZM21 6v6h5M11 15h9M11 20h5" />
      <circle cx="23" cy="24" r="6" fill="var(--icon-accent, #72C7D0)" />
      <path d="m20.5 24 1.7 1.7 3.4-3.6" />
    </>
  ),
  suggestions: (
    <>
      <circle cx="16" cy="16" r="11" fill="currentColor" fillOpacity=".1" />
      <path d="M25.4 10.3a11 11 0 1 1-4.1-4.1" />
      <path
        d="m20.7 10.4-2.2 8.1-8.1 2.2 2.2-8.1 8.1-2.2Z"
        fill="var(--icon-accent, #D8789E)"
      />
      <circle cx="16" cy="16" r="1.3" fill="currentColor" stroke="none" />
      <path d="M27 3v6M24 6h6" />
    </>
  ),
  guidance: (
    <>
      <path
        d="M7 6h18a4 4 0 0 1 4 4v11a4 4 0 0 1-4 4H13l-7 5v-5a4 4 0 0 1-3-4V10a4 4 0 0 1 4-4Z"
        fill="currentColor"
        fillOpacity=".1"
      />
      <path d="M7 6h18a4 4 0 0 1 4 4v11a4 4 0 0 1-4 4H13l-7 5v-5a4 4 0 0 1-3-4V10a4 4 0 0 1 4-4Z" />
      <path d="M13 12a3.1 3.1 0 0 1 6 1c0 2-3 2-3 4" />
      <circle
        cx="16"
        cy="21"
        r="1.2"
        fill="var(--icon-accent, #ED4D6E)"
        stroke="none"
      />
    </>
  ),
  verification: (
    <>
      <path
        d="M16 3 27 8v9c0 5-4 8.7-11 12C9 25.7 5 22 5 17V8l11-5Z"
        fill="currentColor"
        fillOpacity=".1"
      />
      <path d="M16 3 27 8v9c0 5-4 8.7-11 12C9 25.7 5 22 5 17V8l11-5Z" />
      <circle
        cx="16"
        cy="15.5"
        r="6.2"
        fill="var(--icon-accent, #72C7D0)"
        stroke="none"
      />
      <path d="m12.3 15.6 2.5 2.5 5-5.1" />
    </>
  ),
  content: (
    <>
      <rect
        x="4"
        y="4"
        width="24"
        height="24"
        rx="5"
        fill="currentColor"
        fillOpacity=".1"
      />
      <rect x="4" y="4" width="24" height="24" rx="5" />
      <rect
        x="9"
        y="9"
        width="7"
        height="7"
        rx="1.5"
        fill="var(--icon-accent, #D7A3B7)"
        stroke="none"
      />
      <path d="M20 10h3M20 15h3M9 21h14" />
    </>
  ),
  reports: (
    <>
      <path
        d="M9 29V5c5-5 10 5 17 0v14c-7 5-12-5-17 0"
        fill="currentColor"
        fillOpacity=".1"
      />
      <path d="M9 29V5c5-5 10 5 17 0v14c-7 5-12-5-17 0M5 29h8" />
      <path
        d="M18 8v5"
        stroke="var(--icon-accent, #ED4D6E)"
        strokeWidth="2.5"
      />
      <circle
        cx="18"
        cy="16"
        r="1"
        fill="var(--icon-accent, #ED4D6E)"
        stroke="none"
      />
    </>
  ),
  audit: (
    <>
      <rect
        x="6"
        y="6"
        width="20"
        height="23"
        rx="3"
        fill="currentColor"
        fillOpacity=".1"
      />
      <rect x="6" y="6" width="20" height="23" rx="3" />
      <rect
        x="11"
        y="3"
        width="10"
        height="6"
        rx="2"
        fill="var(--icon-accent, #E0B0A4)"
      />
      <path d="m11 16 2 2 3-3M19 17h3m-11 6h11" />
    </>
  ),
  profile: (
    <>
      <circle cx="16" cy="11" r="6" fill="var(--icon-accent, #D7A3B7)" />
      <path
        d="M5 29v-3a8 8 0 0 1 8-8h6a8 8 0 0 1 8 8v3"
        fill="currentColor"
        fillOpacity=".1"
      />
      <path d="M5 29v-3a8 8 0 0 1 8-8h6a8 8 0 0 1 8 8v3" />
    </>
  ),
};

export function ThinkIcon({
  name,
  size = 24,
  className = "",
}: MarkProps & { name: IconName }) {
  return (
    <svg
      viewBox="0 0 32 32"
      width={size}
      height={size}
      className={`think-icon ${className}`.trim()}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {marks[name]}
    </svg>
  );
}

export function WelcomeArt({
  className = "",
  priority = false,
}: {
  className?: string;
  priority?: boolean;
}) {
  return (
    <img
      className={`welcome-art ${className}`.trim()}
      src="/illustrations/thinkmedia-welcome.webp"
      width="960"
      height="877"
      alt=""
      loading={priority ? "eager" : "lazy"}
      fetchPriority={priority ? "high" : "auto"}
      decoding="async"
    />
  );
}
