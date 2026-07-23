import { useCallback, useEffect, useMemo, useState } from "react";
import ReactFlow, { Background, Controls, MiniMap } from "reactflow";
import "reactflow/dist/style.css";
import toast from "react-hot-toast";
import { PlayCircle, History, GitBranch } from "lucide-react";
import { PageContainer, Card, SectionHeading } from "../components/common/Card";
import { PageSkeleton, EmptyState } from "../components/common/Skeleton";
import AgentNode from "../components/workflow/AgentNode";
import { usePolling } from "../hooks/usePolling";
import { endpoints } from "../services/api";
import { timeAgo } from "../utils/format";

const nodeTypes = { agent: AgentNode };

function layoutNodes(rawNodes) {
  const perRow = 5;
  return rawNodes.map((n, idx) => {
    const row = Math.floor(idx / perRow);
    let col = idx % perRow;
    if (row % 2 === 1) col = perRow - 1 - col; // serpentine layout
    return {
      id: n.id,
      type: "agent",
      position: { x: col * 250 + 20, y: row * 150 + 20 },
      data: { id: n.id, label: n.label, status: "idle" },
    };
  });
}

function buildEdges(rawEdges, activePath = []) {
  return rawEdges.map((e) => {
    const isActive = activePath.includes(e.source) && activePath.includes(e.target);
    return {
      id: `${e.source}-${e.target}`,
      source: e.source,
      target: e.target,
      animated: isActive,
      style: { stroke: isActive ? "#06b6d4" : "#2d3748", strokeWidth: isActive ? 2.5 : 1.5 },
    };
  });
}

export default function Workflow() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [running, setRunning] = useState(false);
  const [lastRun, setLastRun] = useState(null);

  const { data: graphDef } = usePolling(() => endpoints.workflowNodes().then((r) => r.data), { intervalMs: 0 });
  const { data: history, refetch: refetchHistory } = usePolling(
    () => endpoints.workflowHistory({ limit: 8 }).then((r) => r.data),
    { intervalMs: 15000 }
  );

  useEffect(() => {
    if (graphDef) {
      setNodes(layoutNodes(graphDef.nodes));
      setEdges(buildEdges(graphDef.edges));
    }
  }, [graphDef]);

  const resetNodeStatuses = useCallback(() => {
    setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, status: "idle" } })));
  }, []);

  async function handleRunWorkflow() {
    if (!graphDef) return;
    setRunning(true);
    resetNodeStatuses();

    try {
      const runPromise = endpoints.runWorkflow({ trigger: "manual" });

      // Animate the agent chain sequentially while the real request is in flight
      const agentIds = graphDef.nodes.filter((n) => n.type === "agent").map((n) => n.id);
      const visited = [];
      for (const id of agentIds) {
        setNodes((nds) => nds.map((n) => (n.id === id ? { ...n, data: { ...n.data, status: "running" } } : n)));
        visited.push(id);
        setEdges(buildEdges(graphDef.edges, visited));
        await new Promise((r) => setTimeout(r, 320));
        setNodes((nds) => nds.map((n) => (n.id === id ? { ...n, data: { ...n.data, status: "success" } } : n)));
      }
      setNodes((nds) =>
        nds.map((n) => (n.id === "mongodb" || n.id === "dashboard-update" ? { ...n, data: { ...n.data, status: "success" } } : n))
      );

      const res = await runPromise;
      setLastRun(res.data);
      toast.success(
        `Workflow ${res.data.run_id} complete — ${res.data.incidents_detected} incident(s) detected.`
      );
      refetchHistory();
    } catch (err) {
      toast.error("Workflow run failed. Check backend connection.");
    } finally {
      setRunning(false);
    }
  }

  const summaryStats = useMemo(() => {
    if (!history) return null;
    const totalIncidents = history.runs.reduce((sum, r) => sum + r.incidents_detected, 0);
    const avgDuration = history.runs.length
      ? Math.round(history.runs.reduce((sum, r) => sum + (r.duration_ms || 0), 0) / history.runs.length)
      : 0;
    return { totalIncidents, avgDuration, totalRuns: history.total };
  }, [history]);

  if (!graphDef) return <PageSkeleton />;

  return (
    <PageContainer>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="text-center py-4">
          <p className="text-2xl font-bold text-white">{summaryStats?.totalRuns ?? "—"}</p>
          <p className="text-xs text-gray-500 uppercase tracking-wide mt-1">Total Workflow Runs</p>
        </Card>
        <Card className="text-center py-4" delay={0.05}>
          <p className="text-2xl font-bold text-cyan-400">{summaryStats?.avgDuration ?? "—"}ms</p>
          <p className="text-xs text-gray-500 uppercase tracking-wide mt-1">Avg. Run Duration</p>
        </Card>
        <Card className="text-center py-4" delay={0.1}>
          <p className="text-2xl font-bold text-violet-400">{summaryStats?.totalIncidents ?? "—"}</p>
          <p className="text-xs text-gray-500 uppercase tracking-wide mt-1">Incidents (last 8 runs)</p>
        </Card>
      </div>

      <Card className="p-0 overflow-hidden">
        <div className="flex items-center justify-between p-5 pb-0">
          <SectionHeading
            title="LangGraph Agent Pipeline"
            subtitle="Infrastructure Health → Log Analysis → Metrics → API Monitoring → Incident Detection → Root Cause → Recommendation → Notification"
          />
          <button
            onClick={handleRunWorkflow}
            disabled={running}
            className="mb-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-500 text-[#0a0e17] text-sm font-semibold hover:opacity-90 transition disabled:opacity-50 shrink-0"
          >
            <PlayCircle size={16} />
            {running ? "Running…" : "Run Workflow"}
          </button>
        </div>
        <div style={{ height: 480 }} className="bg-[#080b12]">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            fitView
            proOptions={{ hideAttribution: true }}
            nodesDraggable={false}
            nodesConnectable={false}
          >
            <Background color="#1f2937" gap={20} />
            <Controls showInteractive={false} />
            <MiniMap
              maskColor="rgba(10,14,23,0.8)"
              nodeColor="#1f2937"
              style={{ background: "#0f1420", border: "1px solid #1f2937" }}
            />
          </ReactFlow>
        </div>
      </Card>

      {lastRun && (
        <Card>
          <SectionHeading title="Last Run Summary" subtitle={lastRun.run_id} />
          <p className="text-sm text-gray-300 mb-4">{lastRun.summary}</p>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            {lastRun.steps.map((step) => (
              <div key={step.agent_id} className="rounded-xl bg-white/[0.03] border border-white/5 p-3">
                <p className="text-xs font-semibold text-gray-200">{step.agent_name}</p>
                <p className="text-[11px] text-gray-500 mt-1">{step.output_summary}</p>
                <p className="text-[10px] text-cyan-400 font-mono mt-1.5">{step.duration_ms}ms</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <SectionHeading title="Run History" subtitle="Most recent workflow executions" action={<History size={16} className="text-gray-500" />} />
        {!history || history.runs.length === 0 ? (
          <EmptyState icon={GitBranch} title="No workflow runs yet" description="Trigger a run above to see history here." />
        ) : (
          <div className="space-y-2">
            {history.runs.map((run) => (
              <div key={run.run_id} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/5 text-xs">
                <div className="flex items-center gap-3 min-w-0">
                  <span className="font-mono text-gray-400">{run.run_id}</span>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 capitalize">{run.status}</span>
                  <span className="text-gray-600 capitalize">{run.trigger}</span>
                </div>
                <div className="flex items-center gap-4 text-gray-500 shrink-0">
                  <span>{run.incidents_detected} incidents</span>
                  <span>{run.duration_ms}ms</span>
                  <span>{timeAgo(run.started_at)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </PageContainer>
  );
}
