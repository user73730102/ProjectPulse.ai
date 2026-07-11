"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { listSubmittals, Submittal, runComplianceCheck } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    pending: { label: "Pending", cls: "bg-slate-500/10 text-slate-400 border-slate-500/20" },
    under_review: { label: "Under Review", cls: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
    approved: { label: "Approved", cls: "badge-approved" },
    rejected: { label: "Rejected", cls: "bg-red-500/10 text-red-500 border-red-500/20" },
  };
  const s = map[status] || map.pending;
  return <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${s.cls}`}>{s.label}</span>;
}

export default function SubmittalsPage() {
  const [submittals, setSubmittals] = useState<Submittal[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningId, setRunningId] = useState<number | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = () => {
    setLoading(true);
    listSubmittals().then(setSubmittals).catch(console.error).finally(() => setLoading(false));
  };

  const handleRunCompliance = async (id: number) => {
    setRunningId(id);
    try {
      const res = await runComplianceCheck(id);
      if (res.error) {
        alert("Compliance check failed: " + res.error);
      } else {
        alert(`Compliance check complete. ${res.ncrs_created} NCR(s) generated.`);
        fetchData();
      }
    } catch (err: any) {
      alert("Error: " + err.message);
    } finally {
      setRunningId(null);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8 fade-up">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Vendor Submittals</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage incoming equipment submittals and run AI compliance checks.</p>
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
                <th className="px-6 py-4 font-medium">Submittal No.</th>
                <th className="px-6 py-4 font-medium">Title & Vendor</th>
                <th className="px-6 py-4 font-medium">Spec Ref</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {submittals.map(sub => (
                <tr key={sub.id} className="hover:bg-secondary/30 transition-colors group">
                  <td className="px-6 py-4">
                    <span className="font-mono text-xs font-semibold text-foreground">{sub.submittal_number}</span>
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-medium text-foreground">{sub.title}</p>
                    <p className="text-xs text-muted-foreground">{sub.vendor_name || "Unknown vendor"}</p>
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-mono text-xs text-muted-foreground bg-secondary px-2 py-1 rounded">
                      {sub.spec_section_ref || "N/A"}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={sub.status} />
                  </td>
                  <td className="px-6 py-4 text-right space-x-3">
                    {(user?.role === "engineer" || user?.role === "pm" || user?.role === "auditor") && sub.status === "pending" && (
                      <button
                        onClick={() => handleRunCompliance(sub.id)}
                        disabled={runningId === sub.id}
                        className="text-xs font-medium text-purple-400 hover:text-purple-300 disabled:opacity-50"
                      >
                        {runningId === sub.id ? "Running..." : "Run AI Check"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {submittals.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                    No submittals found.
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
