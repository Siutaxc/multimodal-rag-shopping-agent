import TraceView from "./TraceView";

export default async function TracePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <TraceView traceId={id} />;
}
