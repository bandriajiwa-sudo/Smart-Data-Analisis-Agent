import tempfile
import os
import time

html_content = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Architecture review for Smart-Data-Analyst-Agent</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="module">
      import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
      mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose" });
    </script>
    <style>
      .seam { stroke-dasharray: 4 4; }
      .leak { stroke: #dc2626; }
      .deep { background: linear-gradient(135deg, #0f172a, #1e293b); }
    </style>
  </head>
  <body class="bg-stone-50 text-slate-900 font-sans">
    <main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
      <header class="border-b border-slate-300 pb-6">
        <h1 class="text-3xl font-serif font-bold text-slate-800">Architecture Review: Smart Data Analyst Agent</h1>
        <p class="text-slate-500 mt-2">August 2026</p>
        <div class="flex space-x-4 mt-6 text-sm items-center">
          <span class="flex items-center"><div class="w-4 h-4 border border-slate-500 mr-2"></div> Module</span>
          <span class="flex items-center"><div class="w-6 h-0 border-t-2 border-dashed border-slate-500 mr-2"></div> Seam</span>
          <span class="flex items-center"><div class="w-6 h-0 border-t-2 border-red-600 mr-2 relative"><div class="absolute right-0 -top-1 w-2 h-2 border-r-2 border-b-2 border-red-600 transform -rotate-45"></div></div> Leak</span>
          <span class="flex items-center"><div class="w-4 h-4 bg-slate-800 mr-2"></div> Deep module</span>
        </div>
      </header>
      
      <section id="candidates" class="space-y-10">
      
        <article class="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-2xl font-serif font-bold text-slate-800">Deepen the LLM Generation Adapter</h2>
            <div class="flex space-x-2">
              <span class="px-3 py-1 bg-emerald-100 text-emerald-800 text-xs font-bold uppercase tracking-wider rounded-full">Strong</span>
              <span class="px-3 py-1 bg-slate-100 text-slate-600 text-xs font-bold uppercase tracking-wider rounded-full">ports & adapters</span>
            </div>
          </div>
          <div class="font-mono text-sm text-slate-500 mb-8">app/agent/nodes/[router.py, sql_generator.py, error_handler.py, answer_generator.py]</div>
          
          <div class="grid grid-cols-2 gap-8 mb-8">
            <div class="rounded-lg border border-slate-200 bg-stone-50 p-4 flex flex-col items-center">
              <h3 class="text-xs uppercase tracking-wider text-slate-500 mb-4">Before: Shallow Modules</h3>
              <pre class="mermaid flex-1">
                flowchart TD
                  A[router.py] -.leak.-> O[ChatOpenAI]
                  B[sql_generator.py] -.leak.-> O
                  C[error_handler.py] -.leak.-> O
                  D[answer_generator.py] -.leak.-> O
                  classDef leak stroke:#dc2626,stroke-width:2px;
                  class A,B,C,D leak
              </pre>
            </div>
            <div class="rounded-lg border border-slate-200 bg-stone-50 p-4 flex flex-col items-center">
              <h3 class="text-xs uppercase tracking-wider text-slate-500 mb-4">After: Deep Adapter</h3>
              <pre class="mermaid flex-1">
                flowchart TD
                  A[Nodes] -->|Interface| LLM[LLM Generation Adapter]
                  LLM -.seam.-> O[ChatOpenAI]
                  classDef deep fill:#1e293b,stroke:#0f172a,color:#fff;
                  class LLM deep
              </pre>
            </div>
          </div>
          
          <p class="mb-4"><strong>Problem:</strong> Agent nodes are shallow wrappers; API configuration and error-handling leak indiscriminately across boundaries.</p>
          <p class="mb-4"><strong>Solution:</strong> Introduce a deep LLM Service adapter behind a clean domain interface.</p>
          <ul class="list-disc pl-5 space-y-2 text-slate-700">
            <li><strong>Locality:</strong> API configurations concentrate in one module.</li>
            <li><strong>Leverage:</strong> One interface constructs JSON prompts.</li>
            <li>Interface shrinks; implementation absorbs API quirks.</li>
          </ul>
        </article>

        <article class="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-2xl font-serif font-bold text-slate-800">Extract Postgres Seam</h2>
            <div class="flex space-x-2">
              <span class="px-3 py-1 bg-amber-100 text-amber-800 text-xs font-bold uppercase tracking-wider rounded-full">Worth exploring</span>
              <span class="px-3 py-1 bg-slate-100 text-slate-600 text-xs font-bold uppercase tracking-wider rounded-full">local-substitutable</span>
            </div>
          </div>
          <div class="font-mono text-sm text-slate-500 mb-8">app/agent/nodes/executor.py, app/db/introspection.py</div>
          
          <div class="grid grid-cols-2 gap-8 mb-8">
            <div class="rounded-lg border border-slate-200 bg-stone-50 p-4 flex flex-col justify-center">
              <h3 class="text-xs uppercase tracking-wider text-slate-500 mb-4">Before: Missing Seam</h3>
              <div class="relative w-full border-l-4 border-red-500 bg-red-50 p-4 flex flex-col justify-center">
                 <span class="font-bold text-slate-800 text-sm">executor.py</span>
                 <br>
                 <span class="text-xs text-slate-600">asyncpg.connect()<br>UUID/Date serializers<br>Graph routing</span>
              </div>
            </div>
            <div class="rounded-lg border border-slate-200 bg-stone-50 p-4 flex flex-col justify-center">
              <h3 class="text-xs uppercase tracking-wider text-slate-500 mb-4">After: Clear Depth</h3>
               <div class="relative w-full border-l-4 border-emerald-500 bg-slate-800 p-4 flex flex-col justify-center">
                 <span class="font-bold text-white text-sm">PgAdapter</span>
                 <br>
                 <span class="text-xs text-slate-400">execute_sql()<br>fetch_schema()</span>
              </div>
            </div>
          </div>
          
          <p class="mb-4"><strong>Problem:</strong> SQL Node executor is extremely shallow; connection pooling and serializers leak into Graph State.</p>
          <p class="mb-4"><strong>Solution:</strong> Deepen the database layer with a distinct DB Adapter.</p>
          <ul class="list-disc pl-5 space-y-2 text-slate-700">
            <li><strong>Locality:</strong> Type serializers isolated to one module.</li>
            <li>Two adapters justify the seam: Pg in production, MockDB in tests.</li>
          </ul>
        </article>

      </section>
      
      <section id="top-recommendation" class="bg-indigo-50 rounded-xl p-8 border border-indigo-100">
        <h2 class="text-xl font-bold text-indigo-900 mb-2">Top Recommendation: Deepen the LLM Generation Adapter</h2>
        <p class="text-indigo-800 mb-2">The recent intense friction around migrating from Google GenAI to OpenRouter proves the LLM injection points are dangerously shallow. Deepening this adapter immediately unlocks structural resilience.</p>
      </section>
      
    </main>
  </body>
</html>"""

temp_dir = tempfile.gettempdir()
file_name = f'architecture-review-{int(time.time())}.html'
file_path = os.path.join(temp_dir, file_name)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f'HTML_REPORT_CREATED: {file_path}')
os.system(f'start {file_path}')
