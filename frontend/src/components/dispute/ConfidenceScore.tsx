"use client";
import { getConfidenceLabel } from "@/lib/utils";

interface ConfidenceScoreProps {
  score: number;
  showLabel?: boolean;
  size?: "sm" | "md" | "lg";
}

/** Conservative bar-style confidence meter. No circles or neon. */
export default function ConfidenceScore({ score, showLabel = true, size = "md" }: ConfidenceScoreProps) {
  const pct   = Math.round(score * 100);
  const label = getConfidenceLabel(score);

  const barColor =
    score >= 0.75 ? "#15803D" :
    score >= 0.55 ? "#B45309" : "#B91C1C";

  const textColor =
    score >= 0.75 ? "#4ADE80" :
    score >= 0.55 ? "#FCD34D" : "#FCA5A5";

  if (size === "lg") {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontSize: "0.65rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "#64748B", marginBottom: "0.25rem" }}>
              Investigation Confidence
            </div>
            {showLabel && (
              <div style={{ fontSize: "0.8rem", fontWeight: 600, color: textColor }}>{label}</div>
            )}
          </div>
          <div style={{ fontSize: "1.25rem", fontWeight: 700, fontFamily: "Inter", color: textColor }}>{pct}%</div>
        </div>
        {/* Bar */}
        <div style={{ height: 6, backgroundColor: "#334155", borderRadius: 2, overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${pct}%`, backgroundColor: barColor, borderRadius: 2, transition: "width 0.5s ease" }} />
        </div>
        {/* Scale */}
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.6rem", color: "#64748B", fontFamily: "ui-monospace, monospace" }}>
          <span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
      <div style={{ flex: 1, height: 4, backgroundColor: "#334155", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${pct}%`, backgroundColor: barColor, borderRadius: 2, transition: "width 0.4s ease" }} />
      </div>
      <div style={{ fontFamily: "ui-monospace, monospace", fontWeight: 600, whiteSpace: "nowrap", fontSize: size === "sm" ? "0.7rem" : "0.75rem", color: textColor }}>
        {pct}%
      </div>
      {showLabel && (
        <div style={{ fontSize: "0.65rem", color: "#64748B" }} className="hidden sm:block">{label}</div>
      )}
    </div>
  );
}
