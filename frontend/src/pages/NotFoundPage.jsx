import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <section className="card mx-auto max-w-xl text-center">
      <h1 className="text-3xl font-bold text-slate-900">404</h1>
      <p className="mt-2 text-slate-600">The page you requested does not exist.</p>
      <Link to="/" className="btn-primary mt-5">
        Back to Home
      </Link>
    </section>
  );
}
