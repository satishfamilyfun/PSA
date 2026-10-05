/** Shown when a view has nothing to display. Plain words: kids use this app. */
export function EmptyState({ message }: { message: string }) {
  return (
    <div role="status" style={{ padding: 24, textAlign: "center", fontSize: 18 }}>
      {message}
    </div>
  );
}
