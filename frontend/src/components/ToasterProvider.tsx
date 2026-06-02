"use client";
import { Toaster } from "react-hot-toast";

export default function ToasterProvider() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        style: {
          background: "#14141f",
          color: "#e2e8f0",
          border: "1px solid #1e1e32",
          borderRadius: "8px",
          fontSize: "13px",
        },
        success: {
          iconTheme: { primary: "#10b981", secondary: "#14141f" },
        },
        error: {
          iconTheme: { primary: "#ef4444", secondary: "#14141f" },
        },
      }}
    />
  );
}
