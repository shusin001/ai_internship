import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import JobCard from '../components/JobCard';
import { EmptyBlock, ErrorBlock, LoadingBlock } from '../components/StateBlock';
import { getJobById } from '../api/jobsApi';
import { getResumeRecommendations, refreshResumeRecommendations } from '../api/resumeApi';
import useAuth from '../hooks/useAuth';

export default function DashboardPage() {
  const { userId } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const tickerCompanies = useMemo(() => {
    const unique = Array.from(
      new Set(
        items
          .map((item) => item?.job?.company)
          .filter((company) => typeof company === 'string' && company.trim())
          .map((company) => company.trim())
      )
    );

    if (!unique.length) return [];

    const expanded = [];
    const targetLength = Math.max(12, unique.length);
    for (let index = 0; index < targetLength; index += 1) {
      expanded.push(unique[index % unique.length]);
    }
    return expanded;
  }, [items]);

  useEffect(() => {
    const run = async () => {
      if (!userId) return;
      setLoading(true);
      setError('');

      try {
        try {
          await refreshResumeRecommendations(userId);
        } catch (_) {
          // Best-effort refresh; fall back to cached recommendations.
        }

        const recommendationData = await getResumeRecommendations(userId);
        const recommendations = recommendationData?.recommendations || [];

        if (!recommendations.length) {
          setItems([]);
          return;
        }

        const detailResponses = await Promise.allSettled(
          recommendations.map((rec) => getJobById(rec.job_id))
        );

        const merged = recommendations
          .map((rec, index) => {
            const detailResult = detailResponses[index];
            if (detailResult.status !== 'fulfilled') return null;
            return {
              recommendation: rec,
              job: detailResult.value
            };
          })
          .filter(Boolean);

        setItems(merged);
      } catch (err) {
        const detail = err?.response?.data?.detail;
        if (detail === 'Resume profile not found.') {
          setError('Resume profile not found. Upload your resume to unlock recommendations.');
        } else {
          setError('Unable to load recommendations right now.');
        }
      } finally {
        setLoading(false);
      }
    };

    run();
  }, [userId]);

  return (
    <section className="space-y-6">
      <div className="card relative min-h-[134px] overflow-hidden bg-gradient-to-r from-brand-50 to-white">
        {tickerCompanies.length ? (
          <div className="pointer-events-none absolute inset-0" aria-hidden="true">
            <div className="company-marquee-layer top-14 md:top-16">
              <div className="company-marquee">
                <div className="company-marquee-track">
                  {tickerCompanies.map((company, index) => (
                    <span key={`primary-${company}-${index}`} className="company-name-bg">
                      {company}
                    </span>
                  ))}
                </div>
                <div className="company-marquee-track">
                  {tickerCompanies.map((company, index) => (
                    <span key={`primary-copy-${company}-${index}`} className="company-name-bg">
                      {company}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="company-marquee-fade" />
          </div>
        ) : null}

        <p className="relative z-10 max-w-3xl text-xl font-semibold leading-snug text-slate-900 md:text-2xl">
          Your top resume-based job recommendations.
        </p>
      </div>

      {loading ? <LoadingBlock text="Loading recommendations..." /> : null}
      {!loading && error ? <ErrorBlock message={error} /> : null}

      {!loading && !error && !items.length ? (
        <EmptyBlock
          title="No recommendations yet"
          description="Upload resume and trigger recommendation generation from backend services."
        />
      ) : null}

      {!loading && !error ? (
        <div className="grid gap-5 md:grid-cols-2">
          {items.map((item) => (
            <JobCard
              key={item.recommendation.job_id}
              job={item.job}
              recommendation={item.recommendation}
            />
          ))}
        </div>
      ) : null}

      <div>
        <Link to="/profile" className="text-sm font-semibold text-brand-700 hover:underline">
          Go to Profile
        </Link>
      </div>
    </section>
  );
}
