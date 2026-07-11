"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { listNCRs, NCR } from "@/lib/api";

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    draft: { label: "Draft", cls: "badge-draft" },
    pending_review: { label: "Review", cls: "badge-pending" },
    approved: { label: "Approved", cls: "badge-approved" },
    voided: { label: "Voided", cls: "bg-red-500/10 text-red-500 border-red-500/20" },
    closed: { label: "Closed", cls: "bg-slate-500/10 text-slate-400 border-slate-500/20" },
  };
  const s = map[status] || map.draft;
  return <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${s.cls}`}>{s.label}</span>;
}

function SeverityBadge({ severity }: { severity: string | null }) {
  const cls = severity === "Critical" ? "badge-critical" : severity === "Major" ? "badge-major" : "badge-minor";
  return <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${cls}`}>{severity || "Minor"}</span>;
}

export default function CompliancePage() {
  const [ncrs, setNCRs] = useState<NCR[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listNCRs().then(setNCRs).catch(console.error).finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8 fade-up">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Non-Conformance Reports</h1>
          <p className="text-sm text-muted-foreground mt-1">Review AI-generated deviations from project specifications.</p>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => <div key={i} className="h-20 bg-card rounded-xl shimmer" />)}
        </div>
      ) : (
        <div className="glass rounded-xl overflow-hidden fade-up gradient-border">
          <table className="w-full text-left text-sm">
            <thead className="bg-secondary/50 border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-6 py-4 font-medium">NCR Number</th>
                <th className="px-6 py-4 font-medium">Severity</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium w-1/2">Deviation Description</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {ncrs.map(ncr => (
                <tr key={ncr.id} className="hover:bg-secondary/30 transition-colors group">
                  <td className="px-6 py-4">
                    <span className="font-mono text-xs font-semibold text-foreground">{ncr.ncr_number}</span>
                  </td>
                  <td className="px-6 py-4">
                    <SeverityBadge severity={ncr.severity} />
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={ncr.status} />
                  </td>
                  <td className="px-6 py-4">
                    <p className="text-muted-foreground line-clamp-1">{ncr.deviation_description}</p>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link href={`/compliance/${ncr.id}`} className="text-blue-400 text-xs font-medium hover:text-blue-300">
                      Review →
                    </Link>
                  </td>
                </tr>
              ))}
              {ncrs.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                    No NCRs found. Run compliance checks on submittals to generate reports.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
