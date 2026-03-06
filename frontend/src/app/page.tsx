import PipelineControls from '@/components/PipelineControls';
import JobCard from '@/components/JobCard';
import { fetchJobs, type Job } from '@/lib/api';

export const dynamic = 'force-dynamic';

export default async function Home() {
  let jobs: Job[] = [];
  try {
    jobs = await fetchJobs();
  } catch (error) {
    console.error("Failed to load jobs:", error);
  }

  return (
    <main className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="mb-10 text-center md:text-left">
        <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight mb-3">
          Auto <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-teal-400">JobAgent</span>
        </h1>
        <p className="text-zinc-400 text-lg">AI-powered tracking & auto application system.</p>
      </header>

      <PipelineControls />

      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            Sourced Jobs
            <span className="bg-zinc-800 text-zinc-300 text-sm py-1 px-3 rounded-full font-medium">
              {jobs.length} total
            </span>
          </h2>
        </div>

        {jobs.length === 0 ? (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-12 text-center">
            <p className="text-zinc-400 text-lg">No jobs found in the database. Run Discovery to scrape new jobs!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {jobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
