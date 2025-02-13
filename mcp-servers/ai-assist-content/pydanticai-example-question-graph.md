Question Graph
==============

Example of a graph for asking and evaluating questions.

Demonstrates:

- [`pydantic_graph`](https://ai.pydantic.dev/../../graph/)

Running the Example
-------------------

With [dependencies installed and environment variables set](https://ai.pydantic.dev/../#usage), run:

pipuv

```
<span></span>```
python<span class="w"> </span>-m<span class="w"> </span>pydantic_ai_examples.question_graph

```
```

```
<span></span>```
uv<span class="w"> </span>run<span class="w"> </span>-m<span class="w"> </span>pydantic_ai_examples.question_graph

```
```

Example Code
------------

question\_graph.py```
<span></span>```
<span class="kn">from</span> <span class="nn">__future__</span> <span class="kn">import</span> <span class="n">annotations</span> <span class="k">as</span> <span class="n">_annotations</span>
<span class="kn">from</span> <span class="nn">dataclasses</span> <span class="kn">import</span> <span class="n">dataclass</span><span class="p">,</span> <span class="n">field</span>
<span class="kn">from</span> <span class="nn">pathlib</span> <span class="kn">import</span> <span class="n">Path</span>
<span class="kn">from</span> <span class="nn">typing</span> <span class="kn">import</span> <span class="n">Annotated</span>
<span class="kn">import</span> <span class="nn">logfire</span>
<span class="kn">from</span> <span class="nn">devtools</span> <span class="kn">import</span> <span class="n">debug</span>
<span class="kn">from</span> <span class="nn">pydantic_graph</span> <span class="kn">import</span> <span class="n">BaseNode</span><span class="p">,</span> <span class="n">Edge</span><span class="p">,</span> <span class="n">End</span><span class="p">,</span> <span class="n">Graph</span><span class="p">,</span> <span class="n">GraphRunContext</span><span class="p">,</span> <span class="n">HistoryStep</span>
<span class="kn">from</span> <span class="nn">pydantic_ai</span> <span class="kn">import</span> <span class="n">Agent</span>
<span class="kn">from</span> <span class="nn">pydantic_ai.format_as_xml</span> <span class="kn">import</span> <span class="n">format_as_xml</span>
<span class="kn">from</span> <span class="nn">pydantic_ai.messages</span> <span class="kn">import</span> <span class="n">ModelMessage</span>
<span class="c1"># 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured</span>
<span class="n">logfire</span><span class="o">.</span><span class="n">configure</span><span class="p">(</span><span class="n">send_to_logfire</span><span class="o">=</span><span class="s1">'if-token-present'</span><span class="p">)</span>
<span class="n">ask_agent</span> <span class="o">=</span> <span class="n">Agent</span><span class="p">(</span><span class="s1">'openai:gpt-4o'</span><span class="p">,</span> <span class="n">result_type</span><span class="o">=</span><span class="nb">str</span><span class="p">)</span>
<span class="nd">@dataclass</span>
<span class="k">class</span> <span class="nc">QuestionState</span><span class="p">:</span>
    <span class="n">question</span><span class="p">:</span> <span class="nb">str</span> <span class="o">|</span> <span class="kc">None</span> <span class="o">=</span> <span class="kc">None</span>
    <span class="n">ask_agent_messages</span><span class="p">:</span> <span class="nb">list</span><span class="p">[</span><span class="n">ModelMessage</span><span class="p">]</span> <span class="o">=</span> <span class="n">field</span><span class="p">(</span><span class="n">default_factory</span><span class="o">=</span><span class="nb">list</span><span class="p">)</span>
    <span class="n">evaluate_agent_messages</span><span class="p">:</span> <span class="nb">list</span><span class="p">[</span><span class="n">ModelMessage</span><span class="p">]</span> <span class="o">=</span> <span class="n">field</span><span class="p">(</span><span class="n">default_factory</span><span class="o">=</span><span class="nb">list</span><span class="p">)</span>
<span class="nd">@dataclass</span>
<span class="k">class</span> <span class="nc">Ask</span><span class="p">(</span><span class="n">BaseNode</span><span class="p">[</span><span class="n">QuestionState</span><span class="p">]):</span>
    <span class="k">async</span> <span class="k">def</span> <span class="nf">run</span><span class="p">(</span><span class="bp">self</span><span class="p">,</span> <span class="n">ctx</span><span class="p">:</span> <span class="n">GraphRunContext</span><span class="p">[</span><span class="n">QuestionState</span><span class="p">])</span> <span class="o">-></span> <span class="n">Answer</span><span class="p">:</span>
        <span class="n">result</span> <span class="o">=</span> <span class="k">await</span> <span class="n">ask_agent</span><span class="o">.</span><span class="n">run</span><span class="p">(</span>
            <span class="s1">'Ask a simple question with a single correct answer.'</span><span class="p">,</span>
            <span class="n">message_history</span><span class="o">=</span><span class="n">ctx</span><span class="o">.</span><span class="n">state</span><span class="o">.</span><span class="n">ask_agent_messages</span><span class="p">,</span>
        <span class="p">)</span>
        <span class="n">ctx</span><span class="o">.</span><span class="n">state</span><span class="o">.</span><span class="n">ask_agent_messages</span> <span class="o">+=</span> <span class="n">result</span><span class="o">.</span><span class="n">all_messages</span><span class="p">()</span>
        <span class="n">ctx</span><span class="o">.</span><span class="n">state</span><span class="o">.</span><span class="n">question</span> <span class="o">=</span> <span class="n">result</span><span class="o">.</span><span class="n">data</span>
        <span class="k">return</span> <span class="n">Answer</span><span class="p">()</span>
<span class="nd">@dataclass</span>
<span class="k">class</span> <span class="nc">Answer</span><span class="p">(</span><span class="n">BaseNode</span><span class="p">[</span><span class="n">QuestionState</span><span class="p">]):</span>
    <span class="n">answer</span><span class="p">:</span> <span class="nb">str</span> <span class="o">|</span> <span class="kc">None</span> <span class="o">=</span> <span class="kc">None</span>
    <span class="k">async</span> <span class="k">def</span> <span class="nf">run</span><span class="p">(</span><span class="bp">self</span><span class="p">,</span> <span class="n">ctx</span><span class="p">:</span> <span class="n">GraphRunContext</span><span class="p">[</span><span class="n">QuestionState</span><span class="p">])</span> <span class="o">-></span> <span class="n">Evaluate</span><span class="p">:</span>
        <span class="k">assert</span> <span class="bp">self</span><span class="o">.</span><span class="n">answer</span> <span class="ow">is</span> <span class="ow">not</span> <span class="kc">None</span>
        <span class="k">return</span> <span class="n">Evaluate</span><span class="p">(</span><span class="bp">self</span><span class="o">.</span><span class="n">answer</span><span class="p">)</span>
<span class="nd">@dataclass</span>
<span class="k">class</span> <span class="nc">EvaluationResult</span><span class="p">:</span>
    <span class="n">correct</span><span class="p">:</span> <span class="nb">bool</span>
    <span class="n">comment</span><span class="p">:</span> <span class="nb">str</span>
<span class="n">evaluate_agent</span> <span class="o">=</span> <span class="n">Agent</span><span class="p">(</span>
    <span class="s1">'openai:gpt-4o'</span><span class="p">,</span>
    <span class="n">result_type</span><span class="o">=</span><span class="n">EvaluationResult</span><span class="p">,</span>
    <span class="n">system_prompt</span><span class="o">=</span><span class="s1">'Given a question and answer, evaluate if the answer is correct.'</span><span class="p">,</span>
<span class="p">)</span>
<span class="nd">@dataclass</span>
<span class="k">class</span> <span class="nc">Evaluate</span><span class="p">(</span><span class="n">BaseNode</span><span class="p">[</span><span class="n">QuestionState</span><span class="p">]):</span>
    <span class="n">answer</span><span class="p">:</span> <span class="nb">str</span>
    <span class="k">async</span> <span class="k">def</span> <span class="nf">run</span><span class="p">(</span>
        <span class="bp">self</span><span class="p">,</span>
        <span class="n">ctx</span><span class="p">:</span> <span class="n">GraphRunContext</span><span class="p">[</span><span class="n">QuestionState</span><span class="p">],</span>
    <span class="p">)</span> <span class="o">-></span> <span class="n">Congratulate</span> <span class="o">|</span> <span class="n">Reprimand</span><span class="p">:</span>
        <span class="k">assert</span> <span class="n">ctx</span><span class="o">.</span><span class="n">state</span><span class="o">.</span><span class="n">question</span> <span class="ow">is</span> <span class="ow">not</span> <span class="kc">None</span>
        <span class="n">result</span> <span class="o">=</span> <span class="k">await</span> <span class="n">evaluate_agent</span><span class="o">.</span><span class="n">run</span><span class="p">(</span>
            <span class="n">format_as_xml</span><span class="p">({</span><span class="s1">'question'</span><span class="p">:</span> <span class="n">ctx</span><span class="o">.</span><span class="n">state</span><span class="o">.</span><span class="n">question</span><span class="p">,</span> <span class="s1">'answer'</span><span class="p">:</span> <span class="bp">self</span><span class="o">.</span><span class="n">answer</span><span class="p">}),</span>
            <span class="n">message_history</span><span class="o">=</span><span class="n">ctx</span><span class="o">.</span><span class="n">state</span><span class="o">.</span><span class="n">evaluate_agent_messages</span><span class="p">,</span>
        <span class="p">)</span>
        <span class="n">ctx</span><span class="o">.</span><span class="n">state</span><span class="o">.</span><span class="n">evaluate_agent_messages</span> <span class="o">+=</span> <span class="n">result</span><span class="o">.</span><span class="n">all_messages</span><span class="p">()</span>
        <span class="k">if</span> <span class="n">result</span><span class="o">.</span><span class="n">data</span><span class="o">.</span><span class="n">correct</span><span class="p">:</span>
            <span class="k">return</span> <span class="n">Congratulate</span><span class="p">(</span><span class="n">result</span><span class="o">.</span><span class="n">data</span><span class="o">.</span><span class="n">comment</span><span class="p">)</span>
        <span class="k">else</span><span class="p">:</span>
            <span class="k">return</span> <span class="n">Reprimand</span><span class="p">(</span><span class="n">result</span><span class="o">.</span><span class="n">data</span><span class="o">.</span><span class="n">comment</span><span class="p">)</span>
<span class="nd">@dataclass</span>
<span class="k">class</span> <span class="nc">Congratulate</span><span class="p">(</span><span class="n">BaseNode</span><span class="p">[</span><span class="n">QuestionState</span><span class="p">,</span> <span class="kc">None</span><span class="p">,</span> <span class="kc">None</span><span class="p">]):</span>
    <span class="n">comment</span><span class="p">:</span> <span class="nb">str</span>
    <span class="k">async</span> <span class="k">def</span> <span class="nf">run</span><span class="p">(</span>
        <span class="bp">self</span><span class="p">,</span> <span class="n">ctx</span><span class="p">:</span> <span class="n">GraphRunContext</span><span class="p">[</span><span class="n">QuestionState</span><span class="p">]</span>
    <span class="p">)</span> <span class="o">-></span> <span class="n">Annotated</span><span class="p">[</span><span class="n">End</span><span class="p">,</span> <span class="n">Edge</span><span class="p">(</span><span class="n">label</span><span class="o">=</span><span class="s1">'success'</span><span class="p">)]:</span>
        <span class="nb">print</span><span class="p">(</span><span class="sa">f</span><span class="s1">'Correct answer! </span><span class="si">{</span><span class="bp">self</span><span class="o">.</span><span class="n">comment</span><span class="si">}</span><span class="s1">'</span><span class="p">)</span>
        <span class="k">return</span> <span class="n">End</span><span class="p">(</span><span class="kc">None</span><span class="p">)</span>
<span class="nd">@dataclass</span>
<span class="k">class</span> <span class="nc">Reprimand</span><span class="p">(</span><span class="n">BaseNode</span><span class="p">[</span><span class="n">QuestionState</span><span class="p">]):</span>
    <span class="n">comment</span><span class="p">:</span> <span class="nb">str</span>
    <span class="k">async</span> <span class="k">def</span> <span class="nf">run</span><span class="p">(</span><span class="bp">self</span><span class="p">,</span> <span class="n">ctx</span><span class="p">:</span> <span class="n">GraphRunContext</span><span class="p">[</span><span class="n">QuestionState</span><span class="p">])</span> <span class="o">-></span> <span class="n">Ask</span><span class="p">:</span>
        <span class="nb">print</span><span class="p">(</span><span class="sa">f</span><span class="s1">'Comment: </span><span class="si">{</span><span class="bp">self</span><span class="o">.</span><span class="n">comment</span><span class="si">}</span><span class="s1">'</span><span class="p">)</span>
        <span class="c1"># > Comment: Vichy is no longer the capital of France.</span>
        <span class="n">ctx</span><span class="o">.</span><span class="n">state</span><span class="o">.</span><span class="n">question</span> <span class="o">=</span> <span class="kc">None</span>
        <span class="k">return</span> <span class="n">Ask</span><span class="p">()</span>
<span class="n">question_graph</span> <span class="o">=</span> <span class="n">Graph</span><span class="p">(</span>
    <span class="n">nodes</span><span class="o">=</span><span class="p">(</span><span class="n">Ask</span><span class="p">,</span> <span class="n">Answer</span><span class="p">,</span> <span class="n">Evaluate</span><span class="p">,</span> <span class="n">Congratulate</span><span class="p">,</span> <span class="n">Reprimand</span><span class="p">),</span> <span class="n">state_type</span><span class="o">=</span><span class="n">QuestionState</span>
<span class="p">)</span>
<span class="k">async</span> <span class="k">def</span> <span class="nf">run_as_continuous</span><span class="p">():</span>
    <span class="n">state</span> <span class="o">=</span> <span class="n">QuestionState</span><span class="p">()</span>
    <span class="n">node</span> <span class="o">=</span> <span class="n">Ask</span><span class="p">()</span>
    <span class="n">history</span><span class="p">:</span> <span class="nb">list</span><span class="p">[</span><span class="n">HistoryStep</span><span class="p">[</span><span class="n">QuestionState</span><span class="p">,</span> <span class="kc">None</span><span class="p">]]</span> <span class="o">=</span> <span class="p">[]</span>
    <span class="k">with</span> <span class="n">logfire</span><span class="o">.</span><span class="n">span</span><span class="p">(</span><span class="s1">'run questions graph'</span><span class="p">):</span>
        <span class="k">while</span> <span class="kc">True</span><span class="p">:</span>
            <span class="n">node</span> <span class="o">=</span> <span class="k">await</span> <span class="n">question_graph</span><span class="o">.</span><span class="n">next</span><span class="p">(</span><span class="n">node</span><span class="p">,</span> <span class="n">history</span><span class="p">,</span> <span class="n">state</span><span class="o">=</span><span class="n">state</span><span class="p">)</span>
            <span class="k">if</span> <span class="nb">isinstance</span><span class="p">(</span><span class="n">node</span><span class="p">,</span> <span class="n">End</span><span class="p">):</span>
                <span class="n">debug</span><span class="p">([</span><span class="n">e</span><span class="o">.</span><span class="n">data_snapshot</span><span class="p">()</span> <span class="k">for</span> <span class="n">e</span> <span class="ow">in</span> <span class="n">history</span><span class="p">])</span>
                <span class="k">break</span>
            <span class="k">elif</span> <span class="nb">isinstance</span><span class="p">(</span><span class="n">node</span><span class="p">,</span> <span class="n">Answer</span><span class="p">):</span>
                <span class="k">assert</span> <span class="n">state</span><span class="o">.</span><span class="n">question</span>
                <span class="n">node</span><span class="o">.</span><span class="n">answer</span> <span class="o">=</span> <span class="nb">input</span><span class="p">(</span><span class="sa">f</span><span class="s1">'</span><span class="si">{</span><span class="n">state</span><span class="o">.</span><span class="n">question</span><span class="si">}</span><span class="s1"> '</span><span class="p">)</span>
            <span class="c1"># otherwise just continue</span>
<span class="k">async</span> <span class="k">def</span> <span class="nf">run_as_cli</span><span class="p">(</span><span class="n">answer</span><span class="p">:</span> <span class="nb">str</span> <span class="o">|</span> <span class="kc">None</span><span class="p">):</span>
    <span class="n">history_file</span> <span class="o">=</span> <span class="n">Path</span><span class="p">(</span><span class="s1">'question_graph_history.json'</span><span class="p">)</span>
    <span class="n">history</span> <span class="o">=</span> <span class="p">(</span>
        <span class="n">question_graph</span><span class="o">.</span><span class="n">load_history</span><span class="p">(</span><span class="n">history_file</span><span class="o">.</span><span class="n">read_bytes</span><span class="p">())</span>
        <span class="k">if</span> <span class="n">history_file</span><span class="o">.</span><span class="n">exists</span><span class="p">()</span>
        <span class="k">else</span> <span class="p">[]</span>
    <span class="p">)</span>
    <span class="k">if</span> <span class="n">history</span><span class="p">:</span>
        <span class="n">last</span> <span class="o">=</span> <span class="n">history</span><span class="p">[</span><span class="o">-</span><span class="mi">1</span><span class="p">]</span>
        <span class="k">assert</span> <span class="n">last</span><span class="o">.</span><span class="n">kind</span> <span class="o">==</span> <span class="s1">'node'</span><span class="p">,</span> <span class="s1">'expected last step to be a node'</span>
        <span class="n">state</span> <span class="o">=</span> <span class="n">last</span><span class="o">.</span><span class="n">state</span>
        <span class="k">assert</span> <span class="n">answer</span> <span class="ow">is</span> <span class="ow">not</span> <span class="kc">None</span><span class="p">,</span> <span class="s1">'answer is required to continue from history'</span>
        <span class="n">node</span> <span class="o">=</span> <span class="n">Answer</span><span class="p">(</span><span class="n">answer</span><span class="p">)</span>
    <span class="k">else</span><span class="p">:</span>
        <span class="n">state</span> <span class="o">=</span> <span class="n">QuestionState</span><span class="p">()</span>
        <span class="n">node</span> <span class="o">=</span> <span class="n">Ask</span><span class="p">()</span>
    <span class="n">debug</span><span class="p">(</span><span class="n">state</span><span class="p">,</span> <span class="n">node</span><span class="p">)</span>
    <span class="k">with</span> <span class="n">logfire</span><span class="o">.</span><span class="n">span</span><span class="p">(</span><span class="s1">'run questions graph'</span><span class="p">):</span>
        <span class="k">while</span> <span class="kc">True</span><span class="p">:</span>
            <span class="n">node</span> <span class="o">=</span> <span class="k">await</span> <span class="n">question_graph</span><span class="o">.</span><span class="n">next</span><span class="p">(</span><span class="n">node</span><span class="p">,</span> <span class="n">history</span><span class="p">,</span> <span class="n">state</span><span class="o">=</span><span class="n">state</span><span class="p">)</span>
            <span class="k">if</span> <span class="nb">isinstance</span><span class="p">(</span><span class="n">node</span><span class="p">,</span> <span class="n">End</span><span class="p">):</span>
                <span class="n">debug</span><span class="p">([</span><span class="n">e</span><span class="o">.</span><span class="n">data_snapshot</span><span class="p">()</span> <span class="k">for</span> <span class="n">e</span> <span class="ow">in</span> <span class="n">history</span><span class="p">])</span>
                <span class="nb">print</span><span class="p">(</span><span class="s1">'Finished!'</span><span class="p">)</span>
                <span class="k">break</span>
            <span class="k">elif</span> <span class="nb">isinstance</span><span class="p">(</span><span class="n">node</span><span class="p">,</span> <span class="n">Answer</span><span class="p">):</span>
                <span class="nb">print</span><span class="p">(</span><span class="n">state</span><span class="o">.</span><span class="n">question</span><span class="p">)</span>
                <span class="k">break</span>
            <span class="c1"># otherwise just continue</span>
    <span class="n">history_file</span><span class="o">.</span><span class="n">write_bytes</span><span class="p">(</span><span class="n">question_graph</span><span class="o">.</span><span class="n">dump_history</span><span class="p">(</span><span class="n">history</span><span class="p">,</span> <span class="n">indent</span><span class="o">=</span><span class="mi">2</span><span class="p">))</span>
<span class="k">if</span> <span class="vm">__name__</span> <span class="o">==</span> <span class="s1">'__main__'</span><span class="p">:</span>
    <span class="kn">import</span> <span class="nn">asyncio</span>
    <span class="kn">import</span> <span class="nn">sys</span>
    <span class="k">try</span><span class="p">:</span>
        <span class="n">sub_command</span> <span class="o">=</span> <span class="n">sys</span><span class="o">.</span><span class="n">argv</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span>
        <span class="k">assert</span> <span class="n">sub_command</span> <span class="ow">in</span> <span class="p">(</span><span class="s1">'continuous'</span><span class="p">,</span> <span class="s1">'cli'</span><span class="p">,</span> <span class="s1">'mermaid'</span><span class="p">)</span>
    <span class="k">except</span> <span class="p">(</span><span class="ne">IndexError</span><span class="p">,</span> <span class="ne">AssertionError</span><span class="p">):</span>
        <span class="nb">print</span><span class="p">(</span>
            <span class="s1">'Usage:</span><span class="se">\n</span><span class="s1">'</span>
            <span class="s1">'  uv run -m pydantic_ai_examples.question_graph mermaid</span><span class="se">\n</span><span class="s1">'</span>
            <span class="s1">'or:</span><span class="se">\n</span><span class="s1">'</span>
            <span class="s1">'  uv run -m pydantic_ai_examples.question_graph continuous</span><span class="se">\n</span><span class="s1">'</span>
            <span class="s1">'or:</span><span class="se">\n</span><span class="s1">'</span>
            <span class="s1">'  uv run -m pydantic_ai_examples.question_graph cli [answer]'</span><span class="p">,</span>
            <span class="n">file</span><span class="o">=</span><span class="n">sys</span><span class="o">.</span><span class="n">stderr</span><span class="p">,</span>
        <span class="p">)</span>
        <span class="n">sys</span><span class="o">.</span><span class="n">exit</span><span class="p">(</span><span class="mi">1</span><span class="p">)</span>
    <span class="k">if</span> <span class="n">sub_command</span> <span class="o">==</span> <span class="s1">'mermaid'</span><span class="p">:</span>
        <span class="nb">print</span><span class="p">(</span><span class="n">question_graph</span><span class="o">.</span><span class="n">mermaid_code</span><span class="p">(</span><span class="n">start_node</span><span class="o">=</span><span class="n">Ask</span><span class="p">))</span>
    <span class="k">elif</span> <span class="n">sub_command</span> <span class="o">==</span> <span class="s1">'continuous'</span><span class="p">:</span>
        <span class="n">asyncio</span><span class="o">.</span><span class="n">run</span><span class="p">(</span><span class="n">run_as_continuous</span><span class="p">())</span>
    <span class="k">else</span><span class="p">:</span>
        <span class="n">a</span> <span class="o">=</span> <span class="n">sys</span><span class="o">.</span><span class="n">argv</span><span class="p">[</span><span class="mi">2</span><span class="p">]</span> <span class="k">if</span> <span class="nb">len</span><span class="p">(</span><span class="n">sys</span><span class="o">.</span><span class="n">argv</span><span class="p">)</span> <span class="o">></span> <span class="mi">2</span> <span class="k">else</span> <span class="kc">None</span>
        <span class="n">asyncio</span><span class="o">.</span><span class="n">run</span><span class="p">(</span><span class="n">run_as_cli</span><span class="p">(</span><span class="n">a</span><span class="p">))</span>

```
```

The mermaid diagram generated in this example looks like this:

```
<pre class="mermaid">```
---
title: question_graph
---
stateDiagram-v2
  [*] --> Ask
  Ask --> Answer: ask the question
  Answer --> Evaluate: answer the question
  Evaluate --> Congratulate
  Evaluate --> Castigate
  Congratulate --> [*]: success
  Castigate --> Ask: try again
```
```