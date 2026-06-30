import React, { useState } from 'react';
import { 
  BarChart3, 
  Clock, 
  Database, 
  Cpu, 
  HelpCircle, 
  ArrowUpRight, 
  TrendingUp, 
  FileText,
  Activity,
  Zap,
  Award
} from 'lucide-react';

export default function AnalyticsView({ documents, analyticsData }) {
  const [hoveredBar, setHoveredBar] = useState(null);
  const [hoveredPoint, setHoveredPoint] = useState(null);

  // If data isn't loaded yet, show a loading placeholder or empty state
  if (!analyticsData) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center text-slate-400">
          <Activity className="w-8 h-8 animate-pulse mb-3" />
          <span>Loading analytics engine...</span>
        </div>
      </div>
    );
  }

  const { topQueries, latencyData, queryVolume } = analyticsData;
  
  const iconMap = {
    docs: FileText,
    chunks: Database,
    vectors: Cpu,
    retrieval: Clock,
    llm: Zap
  };

  const stats = analyticsData.stats.map(s => ({
    ...s,
    icon: iconMap[s.id] || Activity
  }));

  return (
    <div className="flex-1 p-8 bg-slate-50 space-y-8 select-none">
      
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col space-y-1">
          <h2 className="text-xl font-bold text-slate-800">Analytics & Performance Dashboard</h2>
          <p className="text-[13px] text-slate-500">
            Real-time diagnostics tracking vector index metrics, database response rates, and LLM throughput times.
          </p>
        </div>
        <div className="flex items-center space-x-2 bg-white px-3 py-1.5 border border-slate-200 rounded-xl shadow-subtle text-[11px] font-bold text-slate-600">
          <Activity className="w-3.5 h-3.5 text-brand-600" />
          <span>Live Metrics Stream</span>
        </div>
      </div>

      {/* STAT CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-subtle flex flex-col justify-between">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">{s.label}</span>
                <div className="p-1.5 rounded-lg bg-brand-50 text-brand-600 border border-brand-100">
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div>
                <h3 className="text-2xl font-extrabold text-slate-800 tracking-tight">{s.value}</h3>
                <span className={`text-[10px] font-semibold mt-1 inline-block ${
                  s.changeType === 'down' ? 'text-emerald-600' : 'text-brand-600'
                }`}>
                  {s.change}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* CHARTS CONTAINER */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Latency Breakdown Bar Chart (SVG-based) */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-subtle flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-5">
            <div>
              <h3 className="text-[13px] font-extrabold text-slate-800 uppercase tracking-wider">
                Ingestion & RAG Latency Breakdown
              </h3>
              <p className="text-[11px] text-slate-400">Embedding lookup vs. LLM response duration (ms)</p>
            </div>
            {/* Legend */}
            <div className="flex items-center space-x-3 text-[10px] font-bold">
              <div className="flex items-center space-x-1">
                <span className="w-2.5 h-2.5 rounded bg-brand-400" />
                <span className="text-slate-500">Embedding</span>
              </div>
              <div className="flex items-center space-x-1">
                <span className="w-2.5 h-2.5 rounded bg-indigo-500" />
                <span className="text-slate-500">LLM Generation</span>
              </div>
            </div>
          </div>

          {/* SVG Bar Chart */}
          <div className="relative h-64 flex-1">
            <svg className="w-full h-full" viewBox="0 0 500 240" preserveAspectRatio="xMidYMid meet">
              {/* Grid Lines */}
              {[0, 60, 120, 180].map((y, idx) => (
                <line 
                  key={idx} 
                  x1="40" 
                  y1={y + 20} 
                  x2="480" 
                  y2={y + 20} 
                  stroke="#f1f5f9" 
                  strokeWidth="1" 
                />
              ))}

              {/* Bars */}
              {latencyData.map((d, i) => {
                const barWidth = 26;
                const spacing = 62;
                const startX = 50 + i * spacing;
                
                // Max height of SVG chart is 200px, max value 1200ms
                const embedHeight = (d.embed / 1200) * 180;
                const llmHeight = (d.llm / 1200) * 180;

                const embedY = 200 - embedHeight;
                const llmY = embedY - llmHeight;

                return (
                  <g 
                    key={d.label}
                    onMouseEnter={() => setHoveredBar(i)}
                    onMouseLeave={() => setHoveredBar(null)}
                    className="cursor-pointer"
                  >
                    {/* LLM Bar */}
                    <rect 
                      x={startX} 
                      y={llmY} 
                      width={barWidth} 
                      height={llmHeight} 
                      fill={hoveredBar === i ? '#4f46e5' : '#6366f1'} 
                      rx="3" 
                      className="transition-all duration-200"
                    />
                    {/* Embedding Bar */}
                    <rect 
                      x={startX} 
                      y={embedY} 
                      width={barWidth} 
                      height={embedHeight} 
                      fill={hoveredBar === i ? '#2563eb' : '#3b82f6'} 
                      rx="3" 
                      className="transition-all duration-200"
                    />
                    {/* X-axis labels */}
                    <text 
                      x={startX + barWidth/2} 
                      y="220" 
                      textAnchor="middle" 
                      fill="#94a3b8" 
                      fontSize="10" 
                      fontWeight="bold"
                    >
                      {d.label}
                    </text>
                  </g>
                );
              })}

              {/* Tooltip Overlay */}
              {hoveredBar !== null && (
                <g transform={`translate(${50 + hoveredBar * 62 - 10}, 10)`}>
                  <rect width="90" height="38" fill="#1e293b" rx="6" opacity="0.95" />
                  <text x="8" y="14" fill="#ffffff" fontSize="9" fontWeight="bold">
                    LLM: {latencyData[hoveredBar].llm}ms
                  </text>
                  <text x="8" y="28" fill="#93c5fd" fontSize="9" fontWeight="bold">
                    Embed: {latencyData[hoveredBar].embed}ms
                  </text>
                </g>
              )}
            </svg>
          </div>
        </div>

        {/* Daily Queries Line Chart (SVG-based) */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-subtle flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-5">
            <div>
              <h3 className="text-[13px] font-extrabold text-slate-800 uppercase tracking-wider">
                Daily RAG Search Volume
              </h3>
              <p className="text-[11px] text-slate-400">Total processed search queries per day</p>
            </div>
            <div className="text-[11px] bg-slate-50 border px-2 py-0.5 rounded text-slate-500 font-bold">
              Total: {queryVolume.reduce((acc, q) => acc + q.queries, 0)} queries
            </div>
          </div>

          {/* SVG Line Chart */}
          <div className="relative h-64 flex-1">
            <svg className="w-full h-full" viewBox="0 0 500 240" preserveAspectRatio="xMidYMid meet">
              {/* Grid Lines */}
              {[0, 60, 120, 180].map((y, idx) => (
                <line 
                  key={idx} 
                  x1="40" 
                  y1={y + 20} 
                  x2="480" 
                  y2={y + 20} 
                  stroke="#f1f5f9" 
                  strokeWidth="1" 
                />
              ))}

              {/* Graph Line */}
              {(() => {
                const maxQueries = Math.max(...queryVolume.map(q => q.queries), 10);
                const points = queryVolume.map((q, i) => {
                  const x = 50 + i * 65;
                  // Max height 180, scale based on maxQueries
                  const y = 200 - (q.queries / maxQueries) * 180;
                  return { x, y };
                });

                const pathData = points.reduce((acc, p, i) => {
                  return i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
                }, '');

                return (
                  <>
                    {/* Shadow Area under the line */}
                    <path 
                      d={`${pathData} L ${points[points.length-1].x} 200 L ${points[0].x} 200 Z`}
                      fill="url(#gradient-brand)" 
                      opacity="0.15"
                    />
                    {/* Line */}
                    <path 
                      d={pathData} 
                      fill="none" 
                      stroke="#2563eb" 
                      strokeWidth="2.5" 
                      strokeLinecap="round"
                    />

                    {/* Gradient Definition */}
                    <defs>
                      <linearGradient id="gradient-brand" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#2563eb" />
                        <stop offset="100%" stopColor="#2563eb" stopOpacity="0" />
                      </linearGradient>
                    </defs>

                    {/* Nodes / Dots */}
                    {points.map((p, i) => (
                      <g 
                        key={i}
                        onMouseEnter={() => setHoveredPoint(i)}
                        onMouseLeave={() => setHoveredPoint(null)}
                        className="cursor-pointer"
                      >
                        <circle 
                          cx={p.x} 
                          cy={p.y} 
                          r={hoveredPoint === i ? '6' : '4'} 
                          fill={hoveredPoint === i ? '#2563eb' : '#ffffff'} 
                          stroke="#2563eb" 
                          strokeWidth="2" 
                          className="transition-all"
                        />
                        <text 
                          x={p.x} 
                          y="220" 
                          textAnchor="middle" 
                          fill="#94a3b8" 
                          fontSize="9" 
                          fontWeight="bold"
                        >
                          {queryVolume[i].date}
                        </text>
                      </g>
                    ))}
                  </>
                );
              })()}

              {/* Tooltip Overlay */}
              {hoveredPoint !== null && (
                <g transform={`translate(${50 + hoveredPoint * 65 - 10}, 15)`}>
                  <rect width="70" height="26" fill="#1e293b" rx="6" opacity="0.95" />
                  <text x="8" y="16" fill="#ffffff" fontSize="9" fontWeight="bold">
                    Queries: {queryVolume[hoveredPoint].queries}
                  </text>
                </g>
              )}
            </svg>
          </div>
        </div>

      </div>

      {/* TOP QUERIES TABLE */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-subtle space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <Award className="w-4 h-4 text-brand-600" />
            <h3 className="font-extrabold text-[13px] text-slate-800 uppercase tracking-wider">
              High Frequency Queries & Retrieve Accuracy
            </h3>
          </div>
          <span className="text-[11px] text-slate-400 font-medium">Confidence average: {topQueries.length > 0 ? (topQueries.reduce((acc, q) => acc + q.confidence, 0) / topQueries.length).toFixed(1) : 0}%</span>
        </div>

        <div className="divide-y divide-slate-100 overflow-x-auto">
          <table className="w-full text-left text-[12px]">
            <thead>
              <tr className="text-slate-400 font-bold">
                <th className="py-2 pr-4">Search Queries</th>
                <th className="py-2 px-3">Hit Count</th>
                <th className="py-2 px-3">Model Accuracy Score</th>
                <th className="py-2 px-3">Response Latency</th>
                <th className="py-2 pl-4 text-right">Optimization Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {topQueries.map((q, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50 transition-all">
                  <td className="py-3 pr-4 font-semibold text-slate-800">{q.query}</td>
                  <td className="py-3 px-3 text-slate-600 font-mono">{q.count}</td>
                  <td className="py-3 px-3">
                    <span className="font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                      {q.confidence}%
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-500 font-mono">{q.latency}</td>
                  <td className="py-3 pl-4 text-right">
                    <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-bold">
                      Cached & Optimized
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
