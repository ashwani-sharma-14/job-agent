export interface Job {
    id: string;
    title: string;
    company: string;
    location: string;
    source_url: string;
    created_at: string;
    match_score?: number;
    required_skills?: string;
    missing_skills?: string;
    is_analyzed?: boolean;
}

const API_BASE = "http://127.0.0.1:8000";

export async function fetchJobs(): Promise<Job[]> {
    const res = await fetch(`${API_BASE}/jobs`, { cache: 'no-store' });
    if (!res.ok) throw new Error("Failed to fetch jobs");
    return res.json();
}

export async function triggerPipelinePhase(phase: 'discover' | 'clean' | 'analyze' | 'apply') {
    const res = await fetch(`${API_BASE}/agent/${phase}`, {
        method: 'POST',
    });
    if (!res.ok) throw new Error(`Phase ${phase} failed`);
    return res.json();
}
