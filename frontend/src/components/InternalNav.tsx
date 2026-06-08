"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export default function InternalNav() {
  const pathname = usePathname();

  return (
    <nav
      style={{ backgroundColor: "#0B1120", borderBottom: "1px solid #334155" }}
      className="fixed top-0 left-0 right-0 z-50"
    >
      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 h-14 flex items-center gap-8">

        {/* Brand */}
        <Link href="/internal-review" className="flex items-center gap-2.5 shrink-0">
          <div
            style={{ width: 28, height: 28, backgroundColor: "#1E293B", border: "1px solid #334155", borderRadius: 3 }}
            className="flex items-center justify-center"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <rect x="1" y="1" width="5" height="5" rx="1" fill="#2563EB" />
              <rect x="8" y="1" width="5" height="5" rx="1" fill="#2563EB" opacity="0.6" />
              <rect x="1" y="8" width="5" height="5" rx="1" fill="#2563EB" opacity="0.6" />
              <rect x="8" y="8" width="5" height="5" rx="1" fill="#2563EB" opacity="0.3" />
            </svg>
          </div>
          <div className="hidden sm:block">
            <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#F8FAFC", letterSpacing: "-0.01em" }}>
              Dispute Management
            </div>
            <div style={{ fontSize: "0.6rem", color: "#64748B", fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase" }}>
              Operations Console
            </div>
          </div>
        </Link>

        {/* Nav links */}
        <div className="flex items-center h-full">
          <Link
            href="/internal-review"
            style={{
              fontSize: "0.75rem",
              fontWeight: 500,
              padding: "0 0.75rem",
              height: "100%",
              display: "flex",
              alignItems: "center",
              borderBottom: pathname.startsWith("/internal-review") ? "2px solid #2563EB" : "2px solid transparent",
              color: pathname.startsWith("/internal-review") ? "#F8FAFC" : "#64748B",
              transition: "color 0.15s",
            }}
          >
            Case Queue
          </Link>
        </div>

        {/* Right side */}
        <div className="ml-auto flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-1.5" style={{ fontSize: "0.7rem", color: "#64748B" }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "#15803D" }} />
            Systems Operational
          </div>
          <Link
            href="/submit-dispute"
            style={{
              fontSize: "0.7rem",
              color: "#94A3B8",
              border: "1px solid #334155",
              borderRadius: 3,
              padding: "0.3rem 0.75rem",
              transition: "all 0.15s",
            }}
            className="hover:text-white hover:border-slate-400"
          >
            Customer Portal
          </Link>
        </div>
      </div>
    </nav>
  );
}
