import { getFeatureLabel } from '../lib/constants';

/**
 * Horizontal SHAP attribution chart.
 * Positive values extend right in green (#10b981), negative extend left in red (#f43f5e).
 * Center axis divides the bar in half — matches screen 3 and screen 4 designs.
 */
export default function ShapBars({ drivers = [] }) {
  if (!drivers.length) {
    return (
      <p className="font-body-sm text-body-sm text-outline px-space-xs">
        No SHAP data available.
      </p>
    );
  }

  const maxAbs = Math.max(...drivers.map(d => Math.abs(d.shap)), 0.001);

  return (
    <div className="flex flex-col gap-space-sm">
      {/* Axis legend */}
      <div className="flex items-center justify-between text-outline font-label-mono text-label-mono">
        <span className="text-[#f43f5e]">← Dragging Down</span>
        <span className="text-[#10b981]">Pushing Up →</span>
      </div>

      {drivers.map((driver, i) => {
        const isBullish = driver.shap >= 0;
        const barPct = (Math.abs(driver.shap) / maxAbs) * 46; // max 46% of the half-bar
        const label = getFeatureLabel(driver.feature);
        const sign = isBullish ? '+' : '';

        return (
          <div key={i} className="flex flex-col gap-1">
            <div className="flex items-center justify-between font-body-sm text-body-sm">
              <span className="text-on-surface font-medium truncate max-w-[70%]">{label}</span>
              <span className={`font-code-sm text-code-sm font-bold ${isBullish ? 'text-[#10b981]' : 'text-[#f43f5e]'}`}>
                {sign}{driver.shap.toFixed(3)}
              </span>
            </div>
            {/* Two-half bar with center axis */}
            <div className="w-full h-3 bg-surface-container rounded-xs relative flex items-center overflow-hidden">
              {isBullish ? (
                <>
                  {/* left half empty */}
                  <div className="w-1/2 h-full" />
                  {/* center axis */}
                  <div className="w-0.5 h-full bg-outline absolute left-1/2 -translate-x-0.5 z-10" />
                  {/* positive bar grows right */}
                  <div
                    className="h-full bg-[#10b981] rounded-r-xs transition-all duration-500"
                    style={{ width: `${barPct}%` }}
                  />
                </>
              ) : (
                <>
                  {/* center axis */}
                  <div className="w-0.5 h-full bg-outline absolute left-1/2 -translate-x-0.5 z-10" />
                  {/* negative bar grows left from center */}
                  <div className="w-1/2 h-full flex items-center justify-end">
                    <div
                      className="h-full bg-[#f43f5e] rounded-l-xs transition-all duration-500"
                      style={{ width: `${barPct * 2}%` }}
                    />
                  </div>
                  {/* right half empty */}
                  <div className="w-1/2 h-full" />
                </>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
