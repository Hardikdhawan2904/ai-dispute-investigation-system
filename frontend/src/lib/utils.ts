import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Priority, CaseStatus } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency = "INR"): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(dateString: string): string {
  if (!dateString) return "—";
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
    timeZone: "Asia/Kolkata",
  }).format(new Date(dateString));
}

export function formatConfidence(score: number): string {
  return `${(score * 100).toFixed(0)}%`;
}

/** Badge class for priority — light background enterprise style */
export function getPriorityColor(priority: Priority | string): string {
  switch (priority) {
    case "CRITICAL": return "badge badge-critical";
    case "HIGH":     return "badge badge-high";
    case "MEDIUM":   return "badge badge-medium";
    case "LOW":      return "badge badge-low";
    default:         return "badge badge-neutral";
  }
}

/** Badge class for case status */
export function getStatusColor(status: CaseStatus | string): string {
  switch (status) {
    case "Dispute Raised":      return "badge badge-info";
    case "Under Investigation": return "badge badge-medium";
    case "Pending Documents":   return "badge badge-pending";
    case "Escalated":           return "badge badge-escalated";
    case "Resolved":            return "badge badge-resolved";
    case "Rejected":            return "badge badge-rejected";
    case "Closed":              return "badge badge-closed";
    default:                    return "badge badge-neutral";
  }
}

/** Risk tag severity grouping */
export function getRiskTagSeverity(tag: string): "critical" | "warning" | "info" {
  const critical = ["POSSIBLE_FRAUD", "OTP_VERIFIED", "DEVICE_MISMATCH", "SUSPICIOUS_BEHAVIOR", "MERCHANT_BLACKLISTED"];
  const warning  = ["VELOCITY_BREACH", "HIGH_VALUE_TRANSACTION", "INTERNATIONAL_TRANSACTION", "HIGH_PRIORITY_CASE", "FRIENDLY_FRAUD_RISK"];
  if (critical.includes(tag)) return "critical";
  if (warning.includes(tag))  return "warning";
  return "info";
}

/** Confidence level label — operational language, not AI language */
export function getConfidenceLabel(score: number): string {
  if (score >= 0.85) return "Strong";
  if (score >= 0.70) return "Good";
  if (score >= 0.55) return "Moderate";
  if (score >= 0.40) return "Limited";
  return "Low";
}

