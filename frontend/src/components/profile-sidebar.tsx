interface ProfileSidebarProps {
  phase: "upload" | "extracting" | "reviewing" | "gap_filling" | "complete";
  profile: Record<string, unknown> | null;
}

const STEPS = [
  { key: "upload", label: "Upload Resume" },
  { key: "extracting", label: "Skills Extraction" },
  { key: "reviewing", label: "Review & Correct" },
  { key: "gap_filling", label: "Complete Profile" },
];

function getStepState(
  stepKey: string,
  currentPhase: string
): "done" | "active" | "pending" {
  const order = STEPS.map((s) => s.key);
  const currentIdx = order.indexOf(currentPhase);
  const stepIdx = order.indexOf(stepKey);

  if (currentPhase === "complete") return "done";
  if (stepIdx < currentIdx) return "done";
  if (stepIdx === currentIdx) return "active";
  return "pending";
}

function getCompletion(phase: string): number {
  const map: Record<string, number> = {
    upload: 5,
    extracting: 25,
    reviewing: 50,
    gap_filling: 75,
    complete: 100,
  };
  return map[phase] ?? 0;
}

function getSkillTags(profile: Record<string, unknown> | null): string[] {
  if (!profile) return [];
  const skills = profile.skills as Array<{ raw: string }> | undefined;
  return skills?.map((s) => s.raw).slice(0, 8) ?? [];
}

export default function ProfileSidebar({ phase, profile }: ProfileSidebarProps) {
  const completion = getCompletion(phase);
  const skills = getSkillTags(profile);

  return (
    <div className="bg-surface border border-outline rounded-xl p-8 flex flex-col gap-8 sticky top-28 shadow-card">
      {/* Progress */}
      <div>
        <h2 className="font-headline font-extrabold text-xs uppercase tracking-widest text-on-surface-variant mb-6">
          Profile Completion
        </h2>
        <div className="flex flex-col gap-3">
          <div className="flex justify-between text-xs font-bold font-headline uppercase">
            <span className="text-on-surface-variant">Data Integrity</span>
            <span className="text-primary">{completion}%</span>
          </div>
          <div className="w-full h-2 bg-surface-container rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-500"
              style={{ width: `${completion}%` }}
            />
          </div>
        </div>
      </div>

      {/* Steps */}
      <div>
        <h2 className="font-headline font-extrabold text-xs uppercase tracking-widest text-on-surface-variant mb-6">
          Current Progress
        </h2>
        <div className="space-y-3">
          {STEPS.map((step) => {
            const state = getStepState(step.key, phase);
            return (
              <div
                key={step.key}
                className={`flex items-center gap-4 p-4 rounded-lg transition-all duration-200 ${
                  state === "active"
                    ? "bg-surface border border-primary/20 shadow-soft"
                    : state === "done"
                    ? "bg-surface-container border border-outline"
                    : "bg-surface-container border border-outline opacity-50"
                }`}
              >
                {state === "done" && (
                  <svg className="w-5 h-5 text-success flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
                  </svg>
                )}
                {state === "active" && (
                  <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                    <div className="w-2.5 h-2.5 bg-primary rounded-full animate-pulse" />
                  </div>
                )}
                {state === "pending" && (
                  <svg className="w-5 h-5 text-on-surface-variant flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                  </svg>
                )}
                <div className="flex flex-col">
                  <span
                    className={`font-headline font-bold text-sm ${
                      state === "active" ? "text-primary" : state === "done" ? "text-on-surface" : "text-on-surface-variant"
                    }`}
                  >
                    {step.label}
                  </span>
                  <span className="font-body text-[10px] text-on-surface-variant uppercase tracking-wider">
                    {state === "done" ? "Completed" : state === "active" ? "In Progress" : "Pending"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Skills preview */}
      {skills.length > 0 && (
        <div>
          <h2 className="font-headline font-extrabold text-xs uppercase tracking-widest text-on-surface-variant mb-4">
            Extracted Skills
          </h2>
          <div className="flex flex-wrap gap-2">
            {skills.map((skill) => (
              <span
                key={skill}
                className="px-3 py-1.5 bg-primary-container text-on-primary-container font-headline text-[11px] font-bold rounded-lg"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
