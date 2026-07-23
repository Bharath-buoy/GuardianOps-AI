export function Skeleton({ className = "" }) {
  return <div className={`skeleton rounded-lg ${className}`} />;
}

export function PageSkeleton() {
  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
      <Skeleton className="h-80" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Skeleton className="h-64" />
        <Skeleton className="h-64" />
      </div>
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 text-gray-500">
      {Icon && <Icon size={32} className="mb-3 text-gray-600" />}
      <p className="text-sm font-medium text-gray-400">{title}</p>
      {description && <p className="text-xs mt-1 max-w-sm">{description}</p>}
    </div>
  );
}
