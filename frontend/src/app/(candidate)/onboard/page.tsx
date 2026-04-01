export default function OnboardPage() {
  return (
    <div className="max-w-7xl mx-auto px-8 pt-12">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
        <h1 className="font-headline font-bold text-sm tracking-widest uppercase text-primary">
          Candidate Onboarding
        </h1>
      </div>
      <div className="bg-surface rounded-xl p-8 border border-outline shadow-card">
        <p className="text-on-surface-variant font-body">
          Resume upload and onboarding chat will be built in Phase 1A.
        </p>
      </div>
    </div>
  );
}
