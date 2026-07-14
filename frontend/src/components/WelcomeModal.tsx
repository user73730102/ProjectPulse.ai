"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";

export default function WelcomeModal() {
  const [isOpen, setIsOpen] = useState(false);
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Only run on client and if user exists
    if (typeof window !== "undefined" && user) {
      const hasSeen = localStorage.getItem(`pulse_tour_${user.role}`);
      if (!hasSeen) {
        setIsOpen(true);
      }
    }
  }, [user]);

  const handleClose = () => {
    if (user) {
      localStorage.setItem(`pulse_tour_${user.role}`, "true");
    }
    setIsOpen(false);
  };

  if (!isOpen || !user) return null;

  // Role-based content mapping
  const content = {
    engineer: {
      title: "Welcome, Lead Engineer!",
      description: "As an engineer, ProjectPulse AI helps you automate the tedious process of reviewing vendor submittals against your complex specifications.",
      steps: [
        { title: "Extract Specs", desc: "Upload a specification PDF. Our AI automatically chunks it into testable clauses.", action: () => router.push("/documents") },
        { title: "Review Submittals", desc: "Upload vendor equipment docs. The AI instantly flags deviations from the spec.", action: () => router.push("/submittals") },
        { title: "Resolve RFIs", desc: "Use the RFI Assistant to query the entire project corpus instantly.", action: () => router.push("/rfi") }
      ]
    },
    pm: {
      title: "Welcome, Project Manager!",
      description: "ProjectPulse AI gives you a bird's-eye view of project health, specifically focusing on schedule risks and supply chain delays.",
      steps: [
        { title: "Track Delays", desc: "View AI-predicted delays based on real-time supply chain tracking.", action: () => router.push("/schedule") },
        { title: "Supply Chain", desc: "Monitor equipment POs and shipping status with automated risk flagging.", action: () => router.push("/supply-chain") },
        { title: "Review NCRs", desc: "Approve or reject AI-drafted Non-Conformance Reports to keep quality high.", action: () => router.push("/compliance") }
      ]
    },
    auditor: {
      title: "Welcome, Quality Auditor!",
      description: "As an auditor, you ensure that everything built matches the design. Let AI draft your Non-Conformance Reports (NCRs) for you.",
      steps: [
        { title: "Run QA Tests", desc: "Use the Simulator to run a failed commissioning test.", action: () => router.push("/commissioning") },
        { title: "Auto-Draft NCRs", desc: "Watch the AI automatically draft a highly detailed NCR for the failed test.", action: () => router.push("/compliance") },
        { title: "Query Specs", desc: "Use the RFI agent to verify specific clauses during your audit.", action: () => router.push("/rfi") }
      ]
    },
    contractor: {
      title: "Welcome, General Contractor!",
      description: "ProjectPulse AI helps you submit documents faster and track your equipment procurement without manual data entry.",
      steps: [
        { title: "Upload Submittals", desc: "Submit your equipment sheets. The AI will pre-check them before the engineer even sees them.", action: () => router.push("/submittals") },
        { title: "Track Equipment", desc: "Ensure your purchase orders are on track for the required site dates.", action: () => router.push("/supply-chain") },
        { title: "Schedule Risks", desc: "See which tasks are critical path and might be delayed by shipments.", action: () => router.push("/schedule") }
      ]
    }
  };

  const roleContent = content[user.role as keyof typeof content] || content.pm;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 bg-background/80 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="glass rounded-2xl w-full max-w-2xl gradient-border shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
        
        {/* Header */}
        <div className="p-6 border-b border-border bg-gradient-to-r from-blue-500/10 to-purple-500/10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-foreground">{roleContent.title}</h2>
          </div>
          <p className="text-sm text-muted-foreground ml-13">{roleContent.description}</p>
        </div>

        {/* Steps */}
        <div className="p-6 bg-card space-y-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">Recommended Evaluation Path</p>
          <div className="grid gap-4 sm:grid-cols-3">
            {roleContent.steps.map((step, idx) => (
              <div 
                key={idx} 
                onClick={() => {
                  handleClose();
                  step.action();
                }}
                className="p-4 rounded-xl border border-border bg-secondary/30 hover:bg-secondary hover:border-blue-500/50 cursor-pointer transition-all group relative overflow-hidden"
              >
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-500 transform -translate-y-full group-hover:translate-y-0 transition-transform"></div>
                <div className="w-8 h-8 rounded-full bg-background flex items-center justify-center text-xs font-bold text-foreground mb-3 border border-border group-hover:border-blue-500/30">
                  {idx + 1}
                </div>
                <h3 className="text-sm font-semibold text-foreground mb-1">{step.title}</h3>
                <p className="text-[11px] text-muted-foreground leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-border flex justify-end bg-card">
          <button 
            onClick={handleClose}
            className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-all flex items-center gap-2 shadow-lg shadow-blue-500/20"
          >
            Start Exploring
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>
        </div>

      </div>
    </div>
  );
}
