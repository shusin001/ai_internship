import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { analyzeGuidance } from '../api/guidanceApi';
import { EmptyBlock, ErrorBlock, LoadingBlock } from '../components/StateBlock';
import useAuth from '../hooks/useAuth';

export default function GuidancePage() {
  const { userId } = useAuth();
  const { jobId } = useParams();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const run = async () => {
      if (!userId || !jobId) return;
      setLoading(true);
      setError('');

      try {
        const response = await analyzeGuidance(userId, jobId);
        setData(response);
      } catch (err) {
        setError(err?.response?.data?.detail || 'Failed to load guidance report.');
      } finally {
        setLoading(false);
      }
    };

    run();
  }, [jobId, userId]);

  if (loading) return <LoadingBlock text="Analyzing skill gap and roadmap..." />;
  if (error) return <ErrorBlock message={error} />;
  if (!data) return <EmptyBlock title="No guidance report" description="Try again from dashboard." />;

  const phases = data.learning_roadmap || {};
  const resourceLinks = data.resource_links || [];

  return (
    <section className="space-y-6">
      <div className="card">
        <h1 className="text-2xl font-bold text-slate-900">Guidance Report</h1>
        <p className="mt-1 text-sm text-slate-600">Role: {data.job_title}</p>
        {data.message ? (
          <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
            {data.message}
          </p>
        ) : null}
        {data.llm_status ? (
          <p className="mt-2 text-xs text-slate-500">
            LLM Status: {data.llm_status}
          </p>
        ) : null}
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        <div className="card">
          <p className="text-sm text-slate-500">Match Score</p>
          <p className="mt-2 text-3xl font-bold text-brand-700">{Math.round((data.current_match_score || 0) * 100)}%</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">Gap Percentage</p>
          <p className="mt-2 text-3xl font-bold text-amber-600">{data.gap_analysis?.gap_percentage || 0}%</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">Missing Skills</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{data.gap_analysis?.missing_skills?.length || 0}</p>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-900">Missing Skills</h2>
        {(data.gap_analysis?.missing_skills || []).length ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {(data.gap_analysis?.missing_skills || []).map((skill) => (
              <span key={skill} className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
                {skill}
              </span>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-500">No missing skills detected for this role.</p>
        )}
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-900">Learning Roadmap</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {Object.entries(phases).map(([phaseName, tasks]) => (
            <div key={phaseName} className="rounded-xl border border-slate-200 p-4">
              <h3 className="font-semibold text-slate-800">{phaseName.replace('_', ' ').toUpperCase()}</h3>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
                {(tasks || []).map((task, idx) => (
                  <li key={`${phaseName}-${idx}`}>{task}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-900">Preparation Strategy</h2>
        <p className="mt-2 text-sm text-slate-700">
          Estimated time: <span className="font-semibold">{data.preparation_strategy?.estimated_time}</span>
        </p>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <h3 className="font-semibold text-slate-800">Project Suggestions</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
              {(data.preparation_strategy?.project_suggestions || []).map((item, idx) => (
                <li key={`proj-${idx}`}>{item}</li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-slate-800">Certification Suggestions</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
              {(data.preparation_strategy?.certification_suggestions || []).map((item, idx) => (
                <li key={`cert-${idx}`}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-900">Learning Resources</h2>
        {resourceLinks.length ? (
          <div className="mt-3 space-y-2">
            {resourceLinks.map((link, idx) => (
              <a
                key={`${link.url}-${idx}`}
                href={link.url}
                target="_blank"
                rel="noreferrer"
                className="block rounded-lg border border-slate-200 px-3 py-2 text-sm text-brand-700 hover:bg-slate-50"
              >
                {link.title}
              </a>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-500">No resource links available for this report.</p>
        )}
      </div>
    </section>
  );
}
