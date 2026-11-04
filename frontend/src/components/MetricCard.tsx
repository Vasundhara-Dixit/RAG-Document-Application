import React from 'react';

interface MetricCardProps {
  label: string;
  value: string;
  target?: string;
  status?: 'PASS' | 'FLAG' | 'NEUTRAL';
  delta?: string;
  baseline?: string;
  icon?: string;
  unit?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  target,
  status = 'NEUTRAL',
  delta,
  baseline,
  icon = 'analytics',
  unit,
}) => {
  const isPositiveDelta = delta?.startsWith('+');

  return (
    <div className="bg-surface-container-lowest border border-surface-container-high p-space-lg rounded-xl shadow-sm flex flex-col justify-between relative overflow-hidden group hover:shadow-md transition-shadow">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-space-sm">
        <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-widest text-outline font-semibold">
          {label}
        </span>
        <span className="material-symbols-outlined text-[20px] text-palette-plum">
          {icon}
        </span>
      </div>

      {/* Primary Value */}
      <div className="flex items-baseline gap-space-sm my-1">
        <span className="font-code-md text-[32px] leading-tight text-primary font-medium tracking-tight">
          {value}
          {unit && <span className="font-ui-label-sm text-ui-label-sm text-outline ml-1">{unit}</span>}
        </span>
        {target && (
          <span className="font-citation-code text-citation-code text-outline">
            {target}
          </span>
        )}
      </div>

      {/* Delta & Status Footer */}
      <div className="pt-space-sm flex items-center justify-between border-t border-surface-container-high/60 mt-space-xs">
        {delta ? (
          <div
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-citation-code text-citation-code font-medium ${
              isPositiveDelta
                ? 'bg-palette-peach/40 text-palette-plum'
                : 'bg-surface-container text-on-surface-variant'
            }`}
          >
            <span className="material-symbols-outlined text-[13px]">
              {isPositiveDelta ? 'arrow_upward' : 'arrow_downward'}
            </span>
            <span>{delta}</span>
          </div>
        ) : (
          <div
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-citation-code text-citation-code font-semibold ${
              status === 'PASS'
                ? 'bg-primary/10 text-primary'
                : status === 'FLAG'
                ? 'bg-palette-rose/15 text-palette-rose'
                : 'bg-surface-container text-on-surface-variant'
            }`}
          >
            <span className="material-symbols-outlined text-[13px]">
              {status === 'PASS' ? 'check_circle' : 'flag'}
            </span>
            <span>{status}</span>
          </div>
        )}

        {baseline && (
          <span className="font-citation-code text-citation-code text-outline">
            Base: {baseline}
          </span>
        )}
      </div>
    </div>
  );
};
