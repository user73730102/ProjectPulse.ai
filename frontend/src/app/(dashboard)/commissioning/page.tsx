export default function CommissioningPage() {
  return (
    <div className="flex flex-col h-full items-center justify-center p-8 text-center fade-up">
      <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-6">
        <svg className="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
        </svg>
      </div>
      <h1 className="text-2xl font-bold text-foreground mb-3">Commissioning QA Copilot</h1>
      <p className="text-muted-foreground max-w-md mb-8 leading-relaxed">
        This module is currently on our product roadmap. It will provide guided test execution, auto-fill client test records, and auto-generate NCRs for out-of-tolerance readings.
      </p>
      <div className="px-4 py-2 rounded-full border border-border bg-secondary/50 text-sm text-foreground/80 font-medium">
        Coming in Phase 2
      </div>
    </div>
  );
}
