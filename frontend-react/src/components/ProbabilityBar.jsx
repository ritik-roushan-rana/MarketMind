/**
 * Stacked 3-way directional probability bar.
 * Matches screen 3 design: UP (green border/glow when active), FLAT (slate), DOWN (red).
 */
export default function ProbabilityBar({ probs = {}, predictedLabel }) {
  const up   = Math.round((probs.up   ?? 0) * 100);
  const flat = Math.round((probs.flat ?? 0) * 100);
  const down = Math.round((probs.down ?? 0) * 100);

  const segments = [
    {
      key: 'up',
      label: 'UP',
      pct: up,
      activeClass:   'bg-[#10b981]/25 border-2 border-primary shadow-[0_0_12px_rgba(76,215,246,0.35)] text-primary',
      inactiveClass: 'bg-[#10b981]/10 border border-[#10b981]/20 text-on-surface-variant',
      icon: 'arrow_drop_up',
      iconColor: 'text-primary',
      valueColor: 'text-on-surface',
    },
    {
      key: 'flat',
      label: 'FLAT',
      pct: flat,
      activeClass:   'bg-[#64748b]/20 border-2 border-primary shadow-[0_0_12px_rgba(76,215,246,0.35)] text-primary',
      inactiveClass: 'bg-[#64748b]/20 border border-[#64748b]/30 text-on-surface-variant',
      icon: 'drag_handle',
      iconColor: 'text-outline',
      valueColor: 'text-on-surface-variant',
    },
    {
      key: 'down',
      label: 'DOWN',
      pct: down,
      activeClass:   'bg-[#f43f5e]/20 border-2 border-primary shadow-[0_0_12px_rgba(76,215,246,0.35)] text-primary',
      inactiveClass: 'bg-[#f43f5e]/15 border border-[#f43f5e]/25 text-on-surface-variant',
      icon: 'arrow_drop_down',
      iconColor: 'text-[#f43f5e]',
      valueColor: 'text-on-surface-variant',
    },
  ];

  return (
    <div className="relative w-full h-11 bg-surface-container rounded overflow-hidden flex p-1 gap-1 border border-outline-variant/20 shadow-inner">
      {segments.map(seg => {
        const isActive = seg.key === predictedLabel;
        return (
          <div
            key={seg.key}
            className={`relative h-full flex items-center justify-between px-space-sm rounded transition-all duration-500 ${isActive ? seg.activeClass : seg.inactiveClass}`}
            style={{ width: `${seg.pct}%`, minWidth: seg.pct > 0 ? '3rem' : '0' }}
          >
            <div className="flex items-center gap-1.5 truncate">
              <span className={`material-symbols-outlined text-[14px] ${isActive ? seg.iconColor : 'text-outline'}`}>
                {seg.icon}
              </span>
              <span className={`font-label-caps text-label-caps font-bold tracking-wider ${isActive ? '' : 'text-outline'}`}>
                {seg.label}
              </span>
            </div>
            <span className={`font-code-md text-code-md font-bold ${isActive ? seg.valueColor : 'text-on-surface-variant'}`}>
              {seg.pct}%
            </span>
          </div>
        );
      })}
    </div>
  );
}
