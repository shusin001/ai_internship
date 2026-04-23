export function LoadingBlock({ text = 'Loading...' }) {
  return (
    <div className="card text-center">
      <p className="text-slate-600">{text}</p>
    </div>
  );
}

export function EmptyBlock({ title, description }) {
  return (
    <div className="card text-center">
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      <p className="mt-2 text-sm text-slate-600">{description}</p>
    </div>
  );
}

export function ErrorBlock({ message }) {
  return (
    <div className="card border-red-200 bg-red-50 text-red-700">
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}
