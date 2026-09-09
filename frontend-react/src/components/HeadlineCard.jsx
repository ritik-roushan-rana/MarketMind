/**
 * Single headline card — matches the "Based on recent coverage" column in screen 3.
 */
export default function HeadlineCard({ headline, index }) {
  return (
    <article className="p-space-sm rounded bg-surface-container/70 hover:bg-surface-container border border-outline-variant/20 transition-all flex flex-col gap-space-xs">
      <div className="flex items-center justify-between">
        <span className="font-label-mono text-label-mono text-primary font-semibold">
          Article {index + 1}
        </span>
      </div>
      <p className="font-body-md text-body-md text-on-surface font-medium leading-snug">
        "{headline}"
      </p>
    </article>
  );
}
