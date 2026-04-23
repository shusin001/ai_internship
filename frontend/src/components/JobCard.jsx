import { Link } from 'react-router-dom';

export default function JobCard({ job, recommendation }) {
  return (
    <article className="card">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{job?.title || 'Unknown Role'}</h3>
          <p className="mt-1 text-sm text-slate-600">{job?.company || 'Unknown Company'}</p>
          <p className="text-sm text-slate-500">{job?.location || 'Remote/Unspecified'}</p>
        </div>
        <span className="rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold text-brand-700">
          Match {Math.round((recommendation?.score || 0) * 100)}%
        </span>
      </div>

      {recommendation?.match_note ? (
        <p className="mb-4 rounded-lg bg-slate-100 p-3 text-sm text-slate-700">{recommendation.match_note}</p>
      ) : null}

      <div className="flex items-center gap-3">
        <Link to={`/guidance/${recommendation?.job_id || job?._id}`} className="btn-primary">
          View Guidance
        </Link>
        {job?.url ? (
          <a href={job.url} target="_blank" rel="noreferrer" className="btn-secondary">
            Job Link
          </a>
        ) : null}
      </div>
    </article>
  );
}
