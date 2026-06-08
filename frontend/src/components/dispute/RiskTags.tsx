"use client";
import { getRiskTagSeverity } from "@/lib/utils";

const TAG_LABELS: Record<string, string> = {
  HIGH_VALUE_TRANSACTION:    "High Value Transaction",
  INTERNATIONAL_TRANSACTION: "International Transaction",
  POSSIBLE_FRAUD:            "Possible Fraud",
  DUPLICATE_PAYMENT:         "Duplicate Payment",
  FRIENDLY_FRAUD_RISK:       "Friendly Fraud Pattern",
  HIGH_PRIORITY_CASE:        "High Priority",
  OTP_VERIFIED:              "OTP Shared",
  DEVICE_MISMATCH:           "Device Mismatch",
  SUSPICIOUS_BEHAVIOR:       "Suspicious Behaviour",
  CARD_NOT_PRESENT:          "Card Not Present",
  RECURRING_DISPUTE:         "Recurring Charge",
  MERCHANT_BLACKLISTED:      "Blacklisted Merchant",
  VELOCITY_BREACH:           "Velocity Breach",
  AI_UNAVAILABLE:            "Manual Review Required",
};

const SEVERITY_CONFIG = {
  critical: { label: "Critical",      bg: "#FEF2F2", text: "#991B1B", border: "#FECACA", dot: "#B91C1C" },
  warning:  { label: "Moderate",      bg: "#FFFBEB", text: "#92400E", border: "#FDE68A", dot: "#B45309" },
  info:     { label: "Informational", bg: "#EFF6FF", text: "#1D4ED8", border: "#BFDBFE", dot: "#2563EB" },
} as const;

interface RiskTagsProps {
  tags: string[];
  compact?: boolean;
}

export default function RiskTags({ tags, compact = false }: RiskTagsProps) {
  if (!tags || tags.length === 0) {
    return <span style={{ fontSize: "0.75rem", color: "#64748B" }}>No risk indicators identified</span>;
  }

  const grouped: Record<"critical" | "warning" | "info", string[]> = { critical: [], warning: [], info: [] };
  tags.forEach((tag) => { grouped[getRiskTagSeverity(tag)].push(tag); });

  if (compact) {
    return (
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.375rem" }}>
        {tags.map((tag) => {
          const sev = getRiskTagSeverity(tag);
          const cfg = SEVERITY_CONFIG[sev];
          return (
            <span key={tag} style={{ background: cfg.bg, color: cfg.text, border: `1px solid ${cfg.border}`, borderRadius: 3, padding: "0.15rem 0.5rem", fontSize: "0.65rem", fontWeight: 600 }}>
              {TAG_LABELS[tag] ?? tag.replace(/_/g, " ")}
            </span>
          );
        })}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.875rem" }}>
      {(["critical", "warning", "info"] as const).map((sev) => {
        const items = grouped[sev];
        if (items.length === 0) return null;
        const cfg = SEVERITY_CONFIG[sev];
        return (
          <div key={sev}>
            <div style={{ fontSize: "0.6rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em", color: "#64748B", marginBottom: "0.375rem" }}>
              {cfg.label}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
              {items.map((tag) => (
                <div key={tag} style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.35rem 0.625rem", background: cfg.bg, border: `1px solid ${cfg.border}`, borderRadius: 3 }}>
                  <div style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: cfg.dot, flexShrink: 0 }} />
                  <span style={{ fontSize: "0.72rem", fontWeight: 500, color: cfg.text }}>
                    {TAG_LABELS[tag] ?? tag.replace(/_/g, " ")}
                  </span>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
