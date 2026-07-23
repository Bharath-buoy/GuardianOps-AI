import { Outlet, useLocation } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

const PAGE_META = {
  "/": { title: "Dashboard", subtitle: "Real-time infrastructure health overview" },
  "/infrastructure": { title: "Infrastructure", subtitle: "Services, containers, databases & APIs" },
  "/incidents": { title: "Incidents", subtitle: "AI-detected anomalies & root cause analysis" },
  "/analytics": { title: "Analytics", subtitle: "Trends, availability & performance insights" },
  "/workflow": { title: "Agent Workflow", subtitle: "LangGraph multi-agent orchestration" },
  "/about": { title: "About", subtitle: "AI-powered AIOps platform architecture and technology overview" },
};

export default function AppLayout() {
  const location = useLocation();
  const meta = PAGE_META[location.pathname] || { title: "GuardianOps AI" };

  return (
    <div className="flex min-h-screen bg-[#0a0e17]">
      <Sidebar />
      <div className="flex-1 min-w-0">
        <Topbar title={meta.title} subtitle={meta.subtitle} />
        <main>
          <Outlet />
        </main>
      </div>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#141a2a",
            color: "#e5e7eb",
            border: "1px solid #2d3748",
            fontSize: "13px",
          },
        }}
      />
    </div>
  );
}
