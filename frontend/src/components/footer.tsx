export default function Footer() {
  return (
    <footer className="w-full bg-surface-container border-t border-outline mt-auto">
      <div className="flex flex-col md:flex-row justify-between items-center w-full px-12 py-6 gap-4 max-w-full mx-auto">
        <div className="flex items-center gap-4">
          <span className="font-headline font-bold text-on-surface">NIYOG</span>
          <span className="text-on-surface-variant/40">|</span>
          <span className="text-on-surface-variant text-sm font-body">
            Agentic Hiring Platform
          </span>
        </div>
        <div className="flex gap-8 items-center">
          <span className="text-on-surface-variant text-sm font-body">
            &copy; {new Date().getFullYear()} Niyog
          </span>
        </div>
      </div>
    </footer>
  );
}
