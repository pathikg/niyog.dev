export default function DashboardPage() {
  return (
    <div className="max-w-7xl mx-auto px-8 pt-12">
      <h1 className="font-headline font-extrabold text-2xl tracking-tight text-on-surface mb-8">
        Dashboard
      </h1>
      <div className="bg-surface rounded-xl p-8 border border-outline shadow-card">
        <p className="text-on-surface-variant font-body">
          Your profile and matched jobs will appear here after onboarding.
        </p>
      </div>
    </div>
  );
}
