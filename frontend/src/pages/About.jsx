import { ShieldCheck, Cpu, Database, Layers, Target, Github } from "lucide-react";
import { PageContainer, Card, SectionHeading } from "../components/common/Card";

const AGENTS = [
  "Infrastructure Health Agent",
  "Log Analysis Agent",
  "Metrics Agent",
  "API Monitoring Agent",
  "Incident Detection Agent",
  "Root Cause Analysis Agent",
  "Recommendation Agent",
  "Notification Agent",
];

const STACK = {
  Frontend: ["React 19", "Vite", "Tailwind CSS v4", "React Router DOM", "Framer Motion", "Recharts", "React Flow", "Axios"],
  Backend: ["FastAPI", "Python 3.12", "LangGraph", "LangChain", "Motor (async MongoDB)", "Pydantic", "Uvicorn"],
  Database: ["MongoDB Atlas"],
  Deployment: ["Vercel (Frontend)", "Render (Backend)"],
};

export default function About() {
  return (
    <PageContainer>
      <Card className="text-center py-10">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-400 to-violet-500 flex items-center justify-center mx-auto glow-cyan">
          <ShieldCheck size={26} className="text-[#0a0e17]" strokeWidth={2.5} />
        </div>
        <h2 className="text-2xl font-bold text-white mt-4">GuardianOps AI</h2>
        <p className="text-sm text-gray-400 mt-2 max-w-xl mx-auto">
          Cloud-Native AIOps Platform for Intelligent Infrastructure Operations
        </p>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card delay={0.05}>
          <SectionHeading title="Platform Capabilities" />
          <p className="text-sm text-gray-400 leading-relaxed">
            GuardianOps AI continuously monitors infrastructure, services, applications, and system telemetry to provide real-time operational visibility. Its multi-agent AI workflow analyzes metrics, logs, and incidents, identifies potential issues, performs root cause analysis, and delivers actionable recommendations through a unified monitoring dashboard.
          </p>
        </Card>

        {/* <Card delay={0.1}>
          <SectionHeading title="Enterprise Features" action={<Target size={16} className="text-emerald-400" />} />
          <p className="text-sm text-gray-400 leading-relaxed">
            This project is aligned with{" "}
            <span className="text-emerald-400 font-medium">UN Sustainable Development Goal 9</span> —
            Industry, Innovation and Infrastructure. By automating software operations and reducing
            downtime through intelligent observability, GuardianOps AI contributes to building
            resilient digital infrastructure and fostering innovation through AI automation.
          </p>
        </Card> */}
      </div>

      <Card delay={0.15}>
        <SectionHeading title="The 8 AI Agents" subtitle="Orchestrated end-to-end by LangGraph" action={<Cpu size={16} className="text-cyan-400" />} />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {AGENTS.map((agent, idx) => (
            <div key={agent} className="rounded-xl bg-white/[0.03] border border-white/5 p-3 text-center">
              <p className="text-[10px] font-mono text-cyan-400/80 mb-1">{String(idx + 1).padStart(2, "0")}</p>
              <p className="text-xs text-gray-300 font-medium leading-tight">{agent}</p>
            </div>
          ))}
        </div>
      </Card>

      <Card delay={0.2}>
        <SectionHeading title="CORE TECHNOLOGIES" action={<Layers size={16} className="text-violet-400" />} />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(STACK).map(([category, items]) => (
            <div key={category}>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">{category}</p>
              <div className="flex flex-wrap gap-1.5">
                {items.map((item) => (
                  <span key={item} className="text-[11px] px-2 py-1 rounded-lg bg-white/5 text-gray-400 border border-white/5">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card delay={0.25}>
        <SectionHeading title="Architecture Overview" action={<Database size={16} className="text-amber-400" />} />
        <pre className="text-[11px] font-mono text-gray-400 leading-relaxed overflow-x-auto bg-black/30 rounded-xl p-4 border border-white/5">
{`React (Vite) Frontend  ──HTTP/REST──▶  FastAPI Backend
                                          │
                     ┌────────────────────┼────────────────────┐
                     ▼                    ▼                    ▼
            Guardian Agent         LangGraph Multi-Agent   MongoDB Atlas
             (Real-Time Metrics,      Workflow Engine       (services,
              System Logs,            (8 sequential agents)   incidents,
               Telemetry)                                     metrics, logs,
                                                              workflow_runs)`}
        </pre>
      </Card>

      <Card delay={0.3} className="text-center py-6">
        <p className="text-xs text-gray-500">
          GuardianOps AI is an intelligent AIOps platform designed to monitor infrastructure, analyze operational data, detect incidents, and assist operators with AI-powered insights and recommendations in real time.
        </p>
        <div className="flex items-center justify-center gap-1.5 mt-3 text-xs text-gray-600">
          <Github size={13} /> github.com/Bharath-buoy/guardianops-ai
        </div>
      </Card>
    </PageContainer>
  );
}
