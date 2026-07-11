"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getSubmittal, runComplianceCheck, SubmittalDetail, NCRSummary } from "@/lib/api";
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

export default function SubmittalDetailPage() {
  const params = useParams();
  const { user } = useAuth();
  const [sub, setSub] = useState<SubmittalDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const id = Number(params.id);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = () => {
    if (!id) return;
    getSubmittal(id)
      .then(setSub)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  const handleRunCompliance = async () => {
    setRunning(true);
    try {
      const res = await runComplianceCheck(id);
      if (res.error) throw new Error(res.error);
      alert(`AI Check Complete. Generated ${res.ncrs_created} draft NCR(s).`);
      fetchData(); // Refresh to see new NCRs
    } catch (e: any) {
      alert("Check failed: " + e.message);
    } finally {
      setRunning(false);
    }
  };

  if (loading) return <div className="p-8 max-w-5xl mx-auto"><div className="h-64 bg-card rounded-xl shimmer" /></div>;
  if (!sub) return <div className="p-8 max-w-5xl mx-auto text-red-400">Submittal not found or {error}</div>;

  return (
    <div className="p-8 max-w-5xl mx-auto pb-24">
      {/* Header */}
      <div className="mb-6 fade-up flex items-start justify-between">
        <div>
          <Link href="/submittals" className="text-xs text-blue-400 hover:text-blue-300 mb-2 inline-block">← Back to Submittals</Link>
          <div className="flex items-center gap-3 mt-1">
            <h1 className="text-2xl font-bold text-foreground">{sub.title}</h1>
            <StatusBadge status={sub.status} />
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Submittal No: <span className="font-mono text-foreground">{sub.submittal_number}</span>
          </p>
        </div>

        {/* Actions */}
        {(user?.role === "engineer" || user?.role === "pm" || user?.role === "auditor") && sub.status === "pending" && (
          <button
            onClick={handleRunCompliance}
            disabled={running}
            className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-sm font-medium transition-colors shadow-lg shadow-purple-500/20 flex items-center gap-2"
          >
            {running ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Analyzing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Run AI Compliance Check
              </>
            )}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 fade-up">
        {/* Details Card */}
        <div className="lg:col-span-2 glass rounded-xl p-6 gradient-border">
          <h2 className="text-sm font-semibold text-foreground border-b border-border pb-3 mb-4">Submittal Details</h2>
          <div className="grid grid-cols-2 gap-6 mb-6">
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1">Vendor</p>
              <p className="text-sm text-foreground font-medium">{sub.vendor_name || "N/A"}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1">Spec Reference</p>
              <p className="text-sm font-mono text-blue-400 bg-blue-400/10 inline-block px-1.5 py-0.5 rounded">
                {sub.spec_section_ref || "N/A"}
              </p>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1">Submitted At</p>
              <p className="text-sm text-foreground">{new Date(sub.submitted_at).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1">Reviewed At</p>
              <p className="text-sm text-foreground">{sub.reviewed_at ? new Date(sub.reviewed_at).toLocaleString() : "Pending"}</p>
            </div>
          </div>
          
          <div>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-2">Submitted Content / Data</p>
            <div className="bg-secondary/50 rounded-lg p-4 border border-border">
              <p className="text-sm text-foreground whitespace-pre-wrap font-mono leading-relaxed">
                {sub.submitted_value || "No detailed content provided."}
              </p>
            </div>
          </div>
        </div>

        {/* Associated NCRs */}
        <div className="glass rounded-xl p-6 h-fit">
          <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
            <h2 className="text-sm font-semibold text-foreground">Associated NCRs</h2>
            <span className="text-xs font-bold bg-amber-500/10 text-amber-500 px-2 py-0.5 rounded-full">
              {sub.ncrs.length}
            </span>
          </div>
          
          <div className="space-y-3">
            {sub.ncrs.map(ncr => (
              <Link key={ncr.id} href={`/compliance/${ncr.id}`}
                className="block p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors border border-transparent hover:border-border">
                <div className="flex justify-between items-start mb-1.5">
                  <span className="font-mono text-xs font-semibold text-foreground">{ncr.ncr_number}</span>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${
                    ncr.status === 'draft' ? 'bg-slate-500/20 text-slate-400' :
                    ncr.status === 'approved' ? 'bg-emerald-500/20 text-emerald-400' :
                    'bg-blue-500/20 text-blue-400'
                  }`}>
                    {ncr.status.replace("_", " ")}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground line-clamp-2">{ncr.deviation_description}</p>
              </Link>
            ))}
            {sub.ncrs.length === 0 && (
              <p className="text-xs text-muted-foreground text-center py-4">
                No non-conformance reports attached.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
