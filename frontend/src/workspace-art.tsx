// FR06/07/11, NFR05/09: original decorative SVG artwork extends ThinkMedia's marks.
import { ThinkIcon, type IconName } from "./brand";

export function WorkspaceArt({
  kind,
  className = "",
}: {
  kind: IconName;
  className?: string;
}) {
  const accents: Partial<Record<IconName, string>> = {
    verification: "#72c7d0",
    reports: "#d8789e",
    learning: "#718444",
    "listing-board": "#e0b0a4",
    applicants: "#72c7d0",
    organization: "#d7a3b7",
  };
  const accent = accents[kind] || "#d7a3b7";
  return (
    <svg
      className={`workspace-art ${className}`}
      viewBox="0 0 160 128"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <ellipse
        cx="82"
        cy="113"
        rx="57"
        ry="7"
        fill="#402c75"
        fillOpacity=".09"
      />
      <rect
        x="34"
        y="15"
        width="87"
        height="94"
        rx="18"
        transform="rotate(-10 34 15)"
        fill={accent}
      />
      <rect
        x="42"
        y="18"
        width="85"
        height="93"
        rx="17"
        transform="rotate(7 42 18)"
        fill="#fff"
        stroke="#402c75"
        strokeOpacity=".14"
        strokeWidth="1.5"
      />
      <path
        d="m55 40 48 6M54 50l30 4"
        stroke="#e6dff0"
        strokeWidth="5"
        strokeLinecap="round"
      />
      <g transform="translate(59 47) scale(1.7)" color="#402c75">
        <ThinkIcon name={kind} size={32} />
      </g>
      <rect x="111" y="74" width="29" height="29" rx="10" fill={accent} />
      <path
        d="m119 88 5 5 8-10"
        stroke="#402c75"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="28" cy="60" r="5" fill="#8a77a7" fillOpacity=".4" />
      <path
        d="M135 29v10M130 34h10"
        stroke={accent}
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}
