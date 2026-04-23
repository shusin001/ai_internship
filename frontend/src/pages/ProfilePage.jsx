import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getResumeProfile, getResumeRecommendations } from '../api/resumeApi';
import { EmptyBlock, ErrorBlock, LoadingBlock } from '../components/StateBlock';
import useAuth from '../hooks/useAuth';

export default function ProfilePage() {
  const { userId } = useAuth();
  const [profile, setProfile] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const run = async () => {
      if (!userId) return;
      setLoading(true);
      setError('');

      try {
        const profileData = await getResumeProfile(userId);
        setProfile(profileData);

        const recommendationData = await getResumeRecommendations(userId);
        setRecommendations(recommendationData?.recommendations || []);
      } catch (err) {
        const detail = err?.response?.data?.detail;
        if (detail === 'Resume profile not found.') {
          setProfile(null);
          setRecommendations([]);
        } else {
          setError(detail || 'Failed to load profile data.');
        }
      } finally {
        setLoading(false);
      }
    };

    run();
  }, [userId]);

  if (loading) return <LoadingBlock text="Loading profile..." />;
  if (error) return <ErrorBlock message={error} />;

  return (
    <section className="space-y-6">
      <div className="card">
        <h1 className="text-2xl font-bold text-slate-900">Profile</h1>
        <p className="mt-1 text-sm text-slate-600">Manage your resume intelligence and recommendations.</p>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">User Info</h2>
          <dl className="mt-3 space-y-2 text-sm text-slate-700">
            <div>
              <dt className="font-medium text-slate-500">User ID</dt>
              <dd>{userId}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Name</dt>
              <dd>{profile?.name || 'Not available'}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Email</dt>
              <dd>{profile?.email || 'Not available'}</dd>
            </div>
          </dl>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Resume Status</h2>
          <p className="mt-3 text-sm text-slate-700">
            {profile ? 'Resume profile found and processed.' : 'No resume profile found yet.'}
          </p>
          {!profile ? (
            <p className="mt-2 text-sm text-slate-600">
              Register with resume upload to activate recommendations and guidance.
            </p>
          ) : null}
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-slate-900">Stored Recommendations</h2>
          <span className="text-sm text-slate-500">{recommendations.length} items</span>
        </div>

        {!recommendations.length ? (
          <div className="mt-4">
            <EmptyBlock
              title="No recommendations"
              description="Recommendations will appear after resume processing and recommendation generation."
            />
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            {recommendations.map((rec) => (
              <div key={rec.job_id} className="rounded-xl border border-slate-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-slate-900">Job ID: {rec.job_id}</p>
                  <span className="rounded-full bg-brand-100 px-2.5 py-1 text-xs font-semibold text-brand-700">
                    {Math.round((rec.score || 0) * 100)}%
                  </span>
                </div>
                {rec.match_note ? <p className="mt-2 text-sm text-slate-600">{rec.match_note}</p> : null}
                <Link to={`/guidance/${rec.job_id}`} className="mt-3 inline-flex text-sm font-semibold text-brand-700 hover:underline">
                  View Guidance
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
