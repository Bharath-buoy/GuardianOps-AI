import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ShieldCheck, Mail, Lock, User, UserPlus, AlertCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { endpoints } from "../services/api";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [accountExists, setAccountExists] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(true);

  // GuardianOps AI supports exactly one operator account — if one already
  // exists, steer the person to /login instead of showing a form that will
  // just 409.
  useEffect(() => {
    let mounted = true;
    endpoints
      .registrationStatus()
      .then((res) => {
        if (mounted) setAccountExists(res.data.account_exists);
      })
      .catch(() => {})
      .finally(() => {
        if (mounted) setCheckingStatus(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register(name, email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || "Registration failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0e17] px-4">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="w-full max-w-sm glass-panel rounded-2xl p-8"
      >
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-400 to-violet-500 flex items-center justify-center glow-cyan mb-3">
            <ShieldCheck size={22} className="text-[#0a0e17]" strokeWidth={2.5} />
          </div>
          <h1 className="text-lg font-bold text-white">GuardianOps AI</h1>
          <p className="text-xs text-gray-500 mt-1">Create your operator account</p>
        </div>

        {!checkingStatus && accountExists ? (
          <div className="text-center space-y-4">
            <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/25 rounded-xl px-3 py-2.5 text-left">
              <AlertCircle size={14} className="shrink-0" />
              An operator account already exists. GuardianOps AI supports a single account per deployment.
            </div>
            <Link
              to="/login"
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-500 text-[#0a0e17] text-sm font-semibold hover:opacity-90 transition"
            >
              Go to Sign In
            </Link>
          </div>
        ) : (
          <>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5">Full Name</label>
                <div className="relative">
                  <User size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Jane Doe"
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/[0.03] border border-white/10 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/40"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5">Email</label>
                <div className="relative">
                  <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@guardianops.ai"
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/[0.03] border border-white/10 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/40"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5">Password</label>
                <div className="relative">
                  <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="At least 8 characters"
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/[0.03] border border-white/10 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/40"
                  />
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/10 border border-red-500/25 rounded-xl px-3 py-2">
                  <AlertCircle size={14} className="shrink-0" />
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-500 text-[#0a0e17] text-sm font-semibold hover:opacity-90 transition disabled:opacity-50"
              >
                <UserPlus size={16} />
                {submitting ? "Creating account…" : "Create Account"}
              </button>
            </form>

            <p className="text-xs text-gray-500 text-center mt-6">
              Already have an account?{" "}
              <Link to="/login" className="text-cyan-400 hover:text-cyan-300 font-medium">
                Sign in
              </Link>
            </p>
          </>
        )}
      </motion.div>
    </div>
  );
}
