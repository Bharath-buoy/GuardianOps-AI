import { motion } from "framer-motion";

export function Card({ children, className = "", delay = 0, ...props }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay }}
      className={`glass-panel rounded-2xl p-5 ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
}

export function PageContainer({ children }) {
  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6">{children}</div>
  );
}

export function SectionHeading({ title, subtitle, action }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div>
        <h2 className="text-sm font-semibold text-white tracking-wide uppercase">{title}</h2>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
