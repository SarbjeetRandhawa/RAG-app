import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function MarkdownRenderer({ content }) {
  return (
    <div className="text-[13px] break-words leading-relaxed">
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({node, ...props}) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full divide-y divide-slate-200 border border-slate-200 rounded-lg" {...props} />
            </div>
          ),
          thead: ({node, ...props}) => <thead className="bg-slate-50" {...props} />,
          th: ({node, ...props}) => (
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider border-b border-slate-200" {...props} />
          ),
          td: ({node, ...props}) => (
            <td className="px-4 py-3 text-sm text-slate-700 border-b border-slate-100" {...props} />
          ),
          p: ({node, ...props}) => <p className="mb-3 last:mb-0" {...props} />,
          ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-3 space-y-1" {...props} />,
          ol: ({node, ...props}) => <ol className="list-decimal pl-5 mb-3 space-y-1" {...props} />,
          a: ({node, ...props}) => <a className="text-brand-600 hover:underline" {...props} />,
          code: ({node, inline, ...props}) => 
            inline ? (
              <code className="bg-slate-100 text-slate-800 px-1 py-0.5 rounded text-[12px] font-mono" {...props} />
            ) : (
              <code className="block bg-slate-800 text-slate-100 p-3 rounded-lg text-[12px] font-mono overflow-x-auto mb-3" {...props} />
            )
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
