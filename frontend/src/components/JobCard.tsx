import { Job } from '@/lib/api';

export default function JobCard({ job }: { job: Job }) {
    // Parsing skills strings into arrays
    const reqSkills = job.required_skills ? job.required_skills.split(',').map(s => s.trim()) : [];
    const missSkills = job.missing_skills ? job.missing_skills.split(',').map(s => s.trim()) : [];

    // Color coding match score
    let scoreColor = "text-zinc-500 bg-zinc-900 border-zinc-700";
    let scoreLabel = "Unanalyzed";

    if (job.is_analyzed && job.match_score !== undefined) {
        const score = job.match_score;
        if (score >= 0.7) {
            scoreColor = "text-green-400 bg-green-950 border-green-800";
            scoreLabel = `${Math.round(score * 100)}% Match`;
        } else if (score >= 0.4) {
            scoreColor = "text-yellow-400 bg-yellow-950 border-yellow-800";
            scoreLabel = `${Math.round(score * 100)}% Match`;
        } else {
            scoreColor = "text-red-400 bg-red-950 border-red-800";
            scoreLabel = `${Math.round(score * 100)}% Match`;
        }
    }

    const dateStr = new Date(job.created_at).toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });

    return (
        <div className="bg-zinc-900 flex flex-col justify-between border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-colors shadow-lg">

            <div>
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <h3 className="text-xl font-semibold text-white mb-1 line-clamp-2">{job.title}</h3>
                        <p className="text-zinc-400 font-medium">
                            {job.company} • <span className="text-zinc-500">{job.location}</span>
                        </p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs font-bold border ${scoreColor}`}>
                        {scoreLabel}
                    </div>
                </div>

                {reqSkills.length > 0 && (
                    <div className="mb-4">
                        <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Required Core Skills</h4>
                        <div className="flex flex-wrap gap-2">
                            {reqSkills.slice(0, 5).map(skill => (
                                <span key={skill} className="px-2 py-1 bg-zinc-800 text-zinc-300 text-xs rounded-md">
                                    {skill}
                                </span>
                            ))}
                            {reqSkills.length > 5 && (
                                <span className="px-2 py-1 text-zinc-500 text-xs">+{reqSkills.length - 5} more</span>
                            )}
                        </div>
                    </div>
                )}

                {missSkills.length > 0 && (
                    <div className="mb-6">
                        <h4 className="text-xs font-bold text-red-500/70 uppercase tracking-wider mb-2">Missing Skills</h4>
                        <div className="flex flex-wrap gap-2">
                            {missSkills.slice(0, 3).map(skill => (
                                <span key={skill} className="px-2 py-1 bg-red-950 text-red-300/80 border border-red-900/50 text-xs rounded-md">
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <div className="flex items-center justify-between mt-6 pt-4 border-t border-zinc-800/80">
                <span className="text-xs text-zinc-600 font-medium">{dateStr}</span>

                {job.source_url && (
                    <a
                        href={job.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-cyan-400 hover:text-cyan-300 transition-colors flex items-center gap-1"
                    >
                        Open Job Link <span aria-hidden="true">&rarr;</span>
                    </a>
                )}
            </div>
        </div>
    );
}
