'use client';

import { useState } from 'react';
import { triggerPipelinePhase } from '@/lib/api';

export default function PipelineControls() {
    const [loading, setLoading] = useState<string | null>(null);
    const [message, setMessage] = useState<string | null>(null);

    const handleTrigger = async (phase: 'discover' | 'clean' | 'analyze' | 'apply') => {
        setLoading(phase);
        setMessage(null);
        try {
            const res = await triggerPipelinePhase(phase);
            setMessage(`Success: ${res.message}`);
            // In a real app we'd dispatch an event or use SWR/React Query to refresh the job list
            setTimeout(() => window.location.reload(), 2000);
        } catch (err) {
            setMessage(`Error: ${(err as Error).message}`);
        } finally {
            setLoading(null);
        }
    };

    const buttons = [
        { id: 'discover', label: '1. Discover (Scrape)', color: 'bg-blue-600 hover:bg-blue-500' },
        { id: 'clean', label: '2. Clean Data', color: 'bg-teal-600 hover:bg-teal-500' },
        { id: 'analyze', label: '3. Analyze (LLM)', color: 'bg-purple-600 hover:bg-purple-500' },
        { id: 'apply', label: '4. Auto-Apply', color: 'bg-green-600 hover:bg-green-500' },
    ] as const;

    return (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-8 shadow-lg">
            <h2 className="text-xl font-bold text-white mb-4">Pipeline Controls</h2>
            <div className="flex flex-wrap gap-4">
                {buttons.map((btn) => (
                    <button
                        key={btn.id}
                        onClick={() => handleTrigger(btn.id)}
                        disabled={loading !== null}
                        className={`${btn.color} text-white px-5 py-2.5 rounded-lg font-medium transition-all duration-200 shadow-lg shadow-black/20 ${loading === btn.id ? 'opacity-50 animate-pulse cursor-wait' :
                                loading !== null ? 'opacity-50 cursor-not-allowed' : 'active:scale-95'
                            }`}
                    >
                        {loading === btn.id ? 'Running...' : btn.label}
                    </button>
                ))}
            </div>

            {message && (
                <div className={`mt-4 p-3 rounded-lg text-sm font-medium ${message.startsWith('Error') ? 'bg-red-900/30 text-red-200 border border-red-800' : 'bg-green-900/30 text-green-200 border border-green-800'
                    }`}>
                    {message}
                </div>
            )}
        </div>
    );
}
