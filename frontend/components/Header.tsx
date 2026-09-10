export default function Header() {
  return (
    <header className="flex items-start justify-between border-b border-navy-700 pb-5">
      <div>
        <div className="flex items-baseline gap-3">
          <h1 className="font-display text-3xl tracking-tight text-ivory">WASL</h1>
          <span className="font-arabic text-2xl text-gold-400">وصل</span>
        </div>
        <p className="mt-1 font-display italic text-sm text-mute">
          Your Intelligent Bridge Between Countries
        </p>
      </div>

      <div className="flex flex-col items-end gap-1.5">
        <div className="flex items-center gap-2 rounded-full border border-navy-600 bg-navy-900/60 px-3 py-1.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-pulseDot rounded-full bg-success" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
          </span>
          <span className="text-xs tracking-wide text-mute">Network Intelligence Active</span>
        </div>
        <span className="text-[11px] tracking-wide text-mute/70">● Demo Environment</span>
      </div>
    </header>
  );
}
