import { Link } from "react-router-dom";
import { ShieldAlert } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center px-6">
      <ShieldAlert size={40} className="text-cyan-500/60 mb-4" />
      <h1 className="text-3xl font-bold text-white">404</h1>
      <p className="text-sm text-gray-500 mt-2">This page isn't being monitored by GuardianOps AI.</p>
      <Link
        to="/"
        className="mt-6 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-500 text-[#0a0e17] text-sm font-semibold hover:opacity-90 transition"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
