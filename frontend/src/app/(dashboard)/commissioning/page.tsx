"use client";
import { useEffect, useState } from "react";
import { listCommissioningTests, evaluateTest, CommissioningTest } from "@/lib/api";

export default function CommissioningPage() {
  const [tests, setTests] = useState<CommissioningTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [evaluatingId, setEvaluatingId] = useState<number | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = () => {
    setLoading(true);
    listCommissioningTests().then(setTests).catch(console.error).finally(() => setLoading(false));
  };

  const handleEvaluate = async (recordId: number) => {
    setEvaluatingId(recordId);
    try {
      const res = await evaluateTest(recordId);
      if (res.ncr_id) {
        alert(`Test Failed! AI has automatically drafted NCR #${res.ncr_id}.`);
      } else {
        alert("Test Passed! No NCRs generated.");
      }
      fetchData();
    } catch (err: any) {
      alert("Error evaluating test: " + err.message);
    } finally {
      setEvaluatingId(null);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto pb-24">
      {/* Live Beta Banner */}
      <div className="mb-8 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-start gap-4 fade-up">
        <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0 mt-1">
          <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div>
          <h2 className="text-sm font-bold text-emerald-400 uppercase tracking-wider mb-1">Live AI Agent Integration</h2>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-4xl">
            This module is fully hooked up to the backend Commissioning Agent. Clicking "Evaluate Test" will run the AI against the recorded values. If the test fails, it auto-drafts an NCR in the Compliance module!
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between mb-8 fade-up" style={{ animationDelay: "0.1s" }}>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Commissioning QA Copilot</h1>
          <p className="text-sm text-muted-foreground mt-1">Guided test execution and automated as-commissioned documentation.</p>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 fade-up">
          {[1, 2, 3].map(i => <div key={i} className="h-64 bg-card rounded-xl shimmer" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 fade-up" style={{ animationDelay: "0.2s" }}>
          {tests.map((test) => (
            <div key={test.id} className="glass rounded-xl p-6 gradient-border flex flex-col h-full group">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <span className="font-mono text-xs font-semibold text-muted-foreground">{test.id}</span>
                  <h3 className="text-lg font-bold text-foreground mt-1">{test.system}</h3>
                </div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                  test.status === "Passed" ? "badge-approved" : 
                  test.status === "Failed" ? "bg-red-500/10 text-red-500 border-red-500/20" : 
                  "bg-slate-500/10 text-slate-400 border-slate-500/20"
                }`}>
                  {test.status}
                </span>
              </div>

              <div className="flex-1">
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-muted-foreground">Test Progress</span>
                  <span className="font-medium text-foreground">{test.progress}%</span>
                </div>
                <div className="w-full h-2 bg-secondary rounded-full overflow-hidden mb-4">
                  <div 
                    className={`h-full rounded-full ${test.progress === 100 ? "bg-emerald-500" : "bg-blue-500"}`} 
                    style={{ width: `${test.progress}%` }} 
                  />
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="p-3 rounded-lg bg-secondary/30 border border-border">
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Total Points</p>
                    <p className="text-lg font-mono font-semibold text-foreground">{test.totalPoints}</p>
                  </div>
                  <div className={`p-3 rounded-lg border ${test.failedPoints > 0 ? "bg-red-500/10 border-red-500/20" : "bg-secondary/30 border-border"}`}>
                    <p className={`text-[10px] uppercase tracking-wider mb-1 ${test.failedPoints > 0 ? "text-red-400" : "text-muted-foreground"}`}>Failed Points</p>
                    <p className={`text-lg font-mono font-semibold ${test.failedPoints > 0 ? "text-red-400" : "text-foreground"}`}>{test.failedPoints}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-border mt-auto">
                <span className="text-xs text-muted-foreground">Updated {test.lastUpdated.substring(0, 10)}</span>
                {test.record_id && test.status === "Pending" && (
                  <button 
                    onClick={() => handleEvaluate(test.record_id!)}
                    disabled={evaluatingId === test.record_id}
                    className="text-sm font-medium text-emerald-400 hover:text-emerald-300 transition-colors bg-emerald-500/10 px-3 py-1.5 rounded-lg border border-emerald-500/20"
                  >
                    {evaluatingId === test.record_id ? "Evaluating..." : "Evaluate Test Run"}
                  </button>
                )}
                {test.status !== "Pending" && (
                  <span className="text-xs text-muted-foreground italic">Evaluated</span>
                )}
              </div>
            </div>
          ))}
          {tests.length === 0 && (
             <div className="col-span-3 text-center py-12 text-muted-foreground">No test procedures found in database.</div>
          )}
        </div>
      )}
    </div>
  );
}
