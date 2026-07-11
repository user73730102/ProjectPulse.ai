export default function ScheduleRiskPage() {
  return (
    <div className="flex flex-col h-full items-center justify-center p-8 text-center fade-up">
      <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-6">
        <svg className="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h1 className="text-2xl font-bold text-foreground mb-3">Predictive Schedule Risk Engine</h1>
      <p className="text-muted-foreground max-w-md mb-8 leading-relaxed">
        This module is currently on our product roadmap. It will ingest P6/MSP schedules and use multi-agent subroutines to identify weather, procurement, and workforce bottlenecks before they delay the critical path.
      </p>
      <div className="px-4 py-2 rounded-full border border-border bg-secondary/50 text-sm text-foreground/80 font-medium">
        Coming in Phase 2
      </div>
    </div>
  );
}
