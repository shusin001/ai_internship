import { Link } from 'react-router-dom';

export default function LandingPage() {
  return (
    <section className="grid gap-8 md:grid-cols-2 md:items-center">
      <div>
        <span className="inline-flex rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-brand-700">
          Career Guidance Platform
        </span>
        <h1 className="mt-4 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Build your job strategy with resume-based insights.
        </h1>
        <p className="mt-4 max-w-xl text-base text-slate-600">
          Connect your resume, discover aligned jobs, and get clear skill-gap guidance with learning roadmap and preparation strategy.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/register" className="btn-primary">
            Get Started
          </Link>
          <Link to="/login" className="btn-secondary">
            Login
          </Link>
        </div>
      </div>

      <div className="card bg-gradient-to-br from-brand-50 to-white">
        <h2 className="text-xl font-semibold text-slate-900">What you can do</h2>
        <ul className="mt-4 space-y-3 text-sm text-slate-700">
          <li>Resume upload during registration.</li>
          <li>View personalized recommendations with match notes.</li>
          <li>Analyze skill gaps for any selected job.</li>
          <li>Follow structured learning roadmap and strategy.</li>
        </ul>
      </div>
    </section>
  );
}
