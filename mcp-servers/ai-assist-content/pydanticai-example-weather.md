Weather agent
=============

Example of PydanticAI with multiple tools which the LLM needs to call in turn to answer a question.

Demonstrates:

- [tools](https://ai.pydantic.dev/../../tools/)
- [agent dependencies](https://ai.pydantic.dev/../../dependencies/)
- [streaming text responses](https://ai.pydantic.dev/../../results/#streaming-text)
- Building a [Gradio](https://www.gradio.app/) UI for the agent

In this case the idea is a "weather" agent — the user can ask for the weather in multiple locations, the agent will use the `get_lat_lng` tool to get the latitude and longitude of the locations, then use the `get_weather` tool to get the weather for those locations.

Running the Example
-------------------

To run this example properly, you might want to add two extra API keys **(Note if either key is missing, the code will fall back to dummy data, so they're not required)**:

- A weather API key from [tomorrow.io](https://www.tomorrow.io/weather-api/) set via `WEATHER_API_KEY`
- A geocoding API key from [geocode.maps.co](https://geocode.maps.co/) set via `GEO_API_KEY`

With [dependencies installed and environment variables set](https://ai.pydantic.dev/../#usage), run:

pipuv

```
<span></span>```
python<span class="w"> </span>-m<span class="w"> </span>pydantic_ai_examples.weather_agent

```
```

```
<span></span>```
uv<span class="w"> </span>run<span class="w"> </span>-m<span class="w"> </span>pydantic_ai_examples.weather_agent

```
```

Example Code
------------

pydantic\_ai\_examples/weather\_agent.py```
<span></span>```
<span class="kn">from</span> <span class="nn">__future__</span> <span class="kn">import</span> <span class="n">annotations</span> <span class="k">as</span> <span class="n">_annotations</span>
<span class="kn">import</span> <span class="nn">asyncio</span>
<span class="kn">import</span> <span class="nn">os</span>
<span class="kn">from</span> <span class="nn">dataclasses</span> <span class="kn">import</span> <span class="n">dataclass</span>
<span class="kn">from</span> <span class="nn">typing</span> <span class="kn">import</span> <span class="n">Any</span>
<span class="kn">import</span> <span class="nn">logfire</span>
<span class="kn">from</span> <span class="nn">devtools</span> <span class="kn">import</span> <span class="n">debug</span>
<span class="kn">from</span> <span class="nn">httpx</span> <span class="kn">import</span> <span class="n">AsyncClient</span>
<span class="kn">from</span> <span class="nn">pydantic_ai</span> <span class="kn">import</span> <span class="n">Agent</span><span class="p">,</span> <span class="n">ModelRetry</span><span class="p">,</span> <span class="n">RunContext</span>
<span class="c1"># 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured</span>
<span class="n">logfire</span><span class="o">.</span><span class="n">configure</span><span class="p">(</span><span class="n">send_to_logfire</span><span class="o">=</span><span class="s1">'if-token-present'</span><span class="p">)</span>
<span class="nd">@dataclass</span>
<span class="k">class</span> <span class="nc">Deps</span><span class="p">:</span>
    <span class="n">client</span><span class="p">:</span> <span class="n">AsyncClient</span>
    <span class="n">weather_api_key</span><span class="p">:</span> <span class="nb">str</span> <span class="o">|</span> <span class="kc">None</span>
    <span class="n">geo_api_key</span><span class="p">:</span> <span class="nb">str</span> <span class="o">|</span> <span class="kc">None</span>
<span class="n">weather_agent</span> <span class="o">=</span> <span class="n">Agent</span><span class="p">(</span>
    <span class="s1">'openai:gpt-4o'</span><span class="p">,</span>
    <span class="c1"># 'Be concise, reply with one sentence.' is enough for some models (like openai) to use</span>
    <span class="c1"># the below tools appropriately, but others like anthropic and gemini require a bit more direction.</span>
    <span class="n">system_prompt</span><span class="o">=</span><span class="p">(</span>
        <span class="s1">'Be concise, reply with one sentence.'</span>
        <span class="s1">'Use the `get_lat_lng` tool to get the latitude and longitude of the locations, '</span>
        <span class="s1">'then use the `get_weather` tool to get the weather.'</span>
    <span class="p">),</span>
    <span class="n">deps_type</span><span class="o">=</span><span class="n">Deps</span><span class="p">,</span>
    <span class="n">retries</span><span class="o">=</span><span class="mi">2</span><span class="p">,</span>
<span class="p">)</span>
<span class="nd">@weather_agent</span><span class="o">.</span><span class="n">tool</span>
<span class="k">async</span> <span class="k">def</span> <span class="nf">get_lat_lng</span><span class="p">(</span>
    <span class="n">ctx</span><span class="p">:</span> <span class="n">RunContext</span><span class="p">[</span><span class="n">Deps</span><span class="p">],</span> <span class="n">location_description</span><span class="p">:</span> <span class="nb">str</span>
<span class="p">)</span> <span class="o">-></span> <span class="nb">dict</span><span class="p">[</span><span class="nb">str</span><span class="p">,</span> <span class="nb">float</span><span class="p">]:</span>
<span class="w">    </span><span class="sd">"""Get the latitude and longitude of a location.</span>
<span class="sd">    Args:</span>
<span class="sd">        ctx: The context.</span>
<span class="sd">        location_description: A description of a location.</span>
<span class="sd">    """</span>
    <span class="k">if</span> <span class="n">ctx</span><span class="o">.</span><span class="n">deps</span><span class="o">.</span><span class="n">geo_api_key</span> <span class="ow">is</span> <span class="kc">None</span><span class="p">:</span>
        <span class="c1"># if no API key is provided, return a dummy response (London)</span>
        <span class="k">return</span> <span class="p">{</span><span class="s1">'lat'</span><span class="p">:</span> <span class="mf">51.1</span><span class="p">,</span> <span class="s1">'lng'</span><span class="p">:</span> <span class="o">-</span><span class="mf">0.1</span><span class="p">}</span>
    <span class="n">params</span> <span class="o">=</span> <span class="p">{</span>
        <span class="s1">'q'</span><span class="p">:</span> <span class="n">location_description</span><span class="p">,</span>
        <span class="s1">'api_key'</span><span class="p">:</span> <span class="n">ctx</span><span class="o">.</span><span class="n">deps</span><span class="o">.</span><span class="n">geo_api_key</span><span class="p">,</span>
    <span class="p">}</span>
    <span class="k">with</span> <span class="n">logfire</span><span class="o">.</span><span class="n">span</span><span class="p">(</span><span class="s1">'calling geocode API'</span><span class="p">,</span> <span class="n">params</span><span class="o">=</span><span class="n">params</span><span class="p">)</span> <span class="k">as</span> <span class="n">span</span><span class="p">:</span>
        <span class="n">r</span> <span class="o">=</span> <span class="k">await</span> <span class="n">ctx</span><span class="o">.</span><span class="n">deps</span><span class="o">.</span><span class="n">client</span><span class="o">.</span><span class="n">get</span><span class="p">(</span><span class="s1">'https://geocode.maps.co/search'</span><span class="p">,</span> <span class="n">params</span><span class="o">=</span><span class="n">params</span><span class="p">)</span>
        <span class="n">r</span><span class="o">.</span><span class="n">raise_for_status</span><span class="p">()</span>
        <span class="n">data</span> <span class="o">=</span> <span class="n">r</span><span class="o">.</span><span class="n">json</span><span class="p">()</span>
        <span class="n">span</span><span class="o">.</span><span class="n">set_attribute</span><span class="p">(</span><span class="s1">'response'</span><span class="p">,</span> <span class="n">data</span><span class="p">)</span>
    <span class="k">if</span> <span class="n">data</span><span class="p">:</span>
        <span class="k">return</span> <span class="p">{</span><span class="s1">'lat'</span><span class="p">:</span> <span class="n">data</span><span class="p">[</span><span class="mi">0</span><span class="p">][</span><span class="s1">'lat'</span><span class="p">],</span> <span class="s1">'lng'</span><span class="p">:</span> <span class="n">data</span><span class="p">[</span><span class="mi">0</span><span class="p">][</span><span class="s1">'lon'</span><span class="p">]}</span>
    <span class="k">else</span><span class="p">:</span>
        <span class="k">raise</span> <span class="n">ModelRetry</span><span class="p">(</span><span class="s1">'Could not find the location'</span><span class="p">)</span>
<span class="nd">@weather_agent</span><span class="o">.</span><span class="n">tool</span>
<span class="k">async</span> <span class="k">def</span> <span class="nf">get_weather</span><span class="p">(</span><span class="n">ctx</span><span class="p">:</span> <span class="n">RunContext</span><span class="p">[</span><span class="n">Deps</span><span class="p">],</span> <span class="n">lat</span><span class="p">:</span> <span class="nb">float</span><span class="p">,</span> <span class="n">lng</span><span class="p">:</span> <span class="nb">float</span><span class="p">)</span> <span class="o">-></span> <span class="nb">dict</span><span class="p">[</span><span class="nb">str</span><span class="p">,</span> <span class="n">Any</span><span class="p">]:</span>
<span class="w">    </span><span class="sd">"""Get the weather at a location.</span>
<span class="sd">    Args:</span>
<span class="sd">        ctx: The context.</span>
<span class="sd">        lat: Latitude of the location.</span>
<span class="sd">        lng: Longitude of the location.</span>
<span class="sd">    """</span>
    <span class="k">if</span> <span class="n">ctx</span><span class="o">.</span><span class="n">deps</span><span class="o">.</span><span class="n">weather_api_key</span> <span class="ow">is</span> <span class="kc">None</span><span class="p">:</span>
        <span class="c1"># if no API key is provided, return a dummy response</span>
        <span class="k">return</span> <span class="p">{</span><span class="s1">'temperature'</span><span class="p">:</span> <span class="s1">'21 °C'</span><span class="p">,</span> <span class="s1">'description'</span><span class="p">:</span> <span class="s1">'Sunny'</span><span class="p">}</span>
    <span class="n">params</span> <span class="o">=</span> <span class="p">{</span>
        <span class="s1">'apikey'</span><span class="p">:</span> <span class="n">ctx</span><span class="o">.</span><span class="n">deps</span><span class="o">.</span><span class="n">weather_api_key</span><span class="p">,</span>
        <span class="s1">'location'</span><span class="p">:</span> <span class="sa">f</span><span class="s1">'</span><span class="si">{</span><span class="n">lat</span><span class="si">}</span><span class="s1">,</span><span class="si">{</span><span class="n">lng</span><span class="si">}</span><span class="s1">'</span><span class="p">,</span>
        <span class="s1">'units'</span><span class="p">:</span> <span class="s1">'metric'</span><span class="p">,</span>
    <span class="p">}</span>
    <span class="k">with</span> <span class="n">logfire</span><span class="o">.</span><span class="n">span</span><span class="p">(</span><span class="s1">'calling weather API'</span><span class="p">,</span> <span class="n">params</span><span class="o">=</span><span class="n">params</span><span class="p">)</span> <span class="k">as</span> <span class="n">span</span><span class="p">:</span>
        <span class="n">r</span> <span class="o">=</span> <span class="k">await</span> <span class="n">ctx</span><span class="o">.</span><span class="n">deps</span><span class="o">.</span><span class="n">client</span><span class="o">.</span><span class="n">get</span><span class="p">(</span>
            <span class="s1">'https://api.tomorrow.io/v4/weather/realtime'</span><span class="p">,</span> <span class="n">params</span><span class="o">=</span><span class="n">params</span>
        <span class="p">)</span>
        <span class="n">r</span><span class="o">.</span><span class="n">raise_for_status</span><span class="p">()</span>
        <span class="n">data</span> <span class="o">=</span> <span class="n">r</span><span class="o">.</span><span class="n">json</span><span class="p">()</span>
        <span class="n">span</span><span class="o">.</span><span class="n">set_attribute</span><span class="p">(</span><span class="s1">'response'</span><span class="p">,</span> <span class="n">data</span><span class="p">)</span>
    <span class="n">values</span> <span class="o">=</span> <span class="n">data</span><span class="p">[</span><span class="s1">'data'</span><span class="p">][</span><span class="s1">'values'</span><span class="p">]</span>
    <span class="c1"># https://docs.tomorrow.io/reference/data-layers-weather-codes</span>
    <span class="n">code_lookup</span> <span class="o">=</span> <span class="p">{</span>
        <span class="mi">1000</span><span class="p">:</span> <span class="s1">'Clear, Sunny'</span><span class="p">,</span>
        <span class="mi">1100</span><span class="p">:</span> <span class="s1">'Mostly Clear'</span><span class="p">,</span>
        <span class="mi">1101</span><span class="p">:</span> <span class="s1">'Partly Cloudy'</span><span class="p">,</span>
        <span class="mi">1102</span><span class="p">:</span> <span class="s1">'Mostly Cloudy'</span><span class="p">,</span>
        <span class="mi">1001</span><span class="p">:</span> <span class="s1">'Cloudy'</span><span class="p">,</span>
        <span class="mi">2000</span><span class="p">:</span> <span class="s1">'Fog'</span><span class="p">,</span>
        <span class="mi">2100</span><span class="p">:</span> <span class="s1">'Light Fog'</span><span class="p">,</span>
        <span class="mi">4000</span><span class="p">:</span> <span class="s1">'Drizzle'</span><span class="p">,</span>
        <span class="mi">4001</span><span class="p">:</span> <span class="s1">'Rain'</span><span class="p">,</span>
        <span class="mi">4200</span><span class="p">:</span> <span class="s1">'Light Rain'</span><span class="p">,</span>
        <span class="mi">4201</span><span class="p">:</span> <span class="s1">'Heavy Rain'</span><span class="p">,</span>
        <span class="mi">5000</span><span class="p">:</span> <span class="s1">'Snow'</span><span class="p">,</span>
        <span class="mi">5001</span><span class="p">:</span> <span class="s1">'Flurries'</span><span class="p">,</span>
        <span class="mi">5100</span><span class="p">:</span> <span class="s1">'Light Snow'</span><span class="p">,</span>
        <span class="mi">5101</span><span class="p">:</span> <span class="s1">'Heavy Snow'</span><span class="p">,</span>
        <span class="mi">6000</span><span class="p">:</span> <span class="s1">'Freezing Drizzle'</span><span class="p">,</span>
        <span class="mi">6001</span><span class="p">:</span> <span class="s1">'Freezing Rain'</span><span class="p">,</span>
        <span class="mi">6200</span><span class="p">:</span> <span class="s1">'Light Freezing Rain'</span><span class="p">,</span>
        <span class="mi">6201</span><span class="p">:</span> <span class="s1">'Heavy Freezing Rain'</span><span class="p">,</span>
        <span class="mi">7000</span><span class="p">:</span> <span class="s1">'Ice Pellets'</span><span class="p">,</span>
        <span class="mi">7101</span><span class="p">:</span> <span class="s1">'Heavy Ice Pellets'</span><span class="p">,</span>
        <span class="mi">7102</span><span class="p">:</span> <span class="s1">'Light Ice Pellets'</span><span class="p">,</span>
        <span class="mi">8000</span><span class="p">:</span> <span class="s1">'Thunderstorm'</span><span class="p">,</span>
    <span class="p">}</span>
    <span class="k">return</span> <span class="p">{</span>
        <span class="s1">'temperature'</span><span class="p">:</span> <span class="sa">f</span><span class="s1">'</span><span class="si">{</span><span class="n">values</span><span class="p">[</span><span class="s2">"temperatureApparent"</span><span class="p">]</span><span class="si">:</span><span class="s1">0.0f</span><span class="si">}</span><span class="s1">°C'</span><span class="p">,</span>
        <span class="s1">'description'</span><span class="p">:</span> <span class="n">code_lookup</span><span class="o">.</span><span class="n">get</span><span class="p">(</span><span class="n">values</span><span class="p">[</span><span class="s1">'weatherCode'</span><span class="p">],</span> <span class="s1">'Unknown'</span><span class="p">),</span>
    <span class="p">}</span>
<span class="k">async</span> <span class="k">def</span> <span class="nf">main</span><span class="p">():</span>
    <span class="k">async</span> <span class="k">with</span> <span class="n">AsyncClient</span><span class="p">()</span> <span class="k">as</span> <span class="n">client</span><span class="p">:</span>
        <span class="c1"># create a free API key at https://www.tomorrow.io/weather-api/</span>
        <span class="n">weather_api_key</span> <span class="o">=</span> <span class="n">os</span><span class="o">.</span><span class="n">getenv</span><span class="p">(</span><span class="s1">'WEATHER_API_KEY'</span><span class="p">)</span>
        <span class="c1"># create a free API key at https://geocode.maps.co/</span>
        <span class="n">geo_api_key</span> <span class="o">=</span> <span class="n">os</span><span class="o">.</span><span class="n">getenv</span><span class="p">(</span><span class="s1">'GEO_API_KEY'</span><span class="p">)</span>
        <span class="n">deps</span> <span class="o">=</span> <span class="n">Deps</span><span class="p">(</span>
            <span class="n">client</span><span class="o">=</span><span class="n">client</span><span class="p">,</span> <span class="n">weather_api_key</span><span class="o">=</span><span class="n">weather_api_key</span><span class="p">,</span> <span class="n">geo_api_key</span><span class="o">=</span><span class="n">geo_api_key</span>
        <span class="p">)</span>
        <span class="n">result</span> <span class="o">=</span> <span class="k">await</span> <span class="n">weather_agent</span><span class="o">.</span><span class="n">run</span><span class="p">(</span>
            <span class="s1">'What is the weather like in London and in Wiltshire?'</span><span class="p">,</span> <span class="n">deps</span><span class="o">=</span><span class="n">deps</span>
        <span class="p">)</span>
        <span class="n">debug</span><span class="p">(</span><span class="n">result</span><span class="p">)</span>
        <span class="nb">print</span><span class="p">(</span><span class="s1">'Response:'</span><span class="p">,</span> <span class="n">result</span><span class="o">.</span><span class="n">data</span><span class="p">)</span>
<span class="k">if</span> <span class="vm">__name__</span> <span class="o">==</span> <span class="s1">'__main__'</span><span class="p">:</span>
    <span class="n">asyncio</span><span class="o">.</span><span class="n">run</span><span class="p">(</span><span class="n">main</span><span class="p">())</span>

```
```

Running the UI
--------------

You can build multi-turn chat applications for your agent with [Gradio](https://www.gradio.app/), a framework for building AI web applications entirely in python. Gradio comes with built-in chat components and agent support so the entire UI will be implemented in a single python file!

Here's what the UI looks like for the weather agent:

 

Note, to run the UI, you'll need Python 3.10+.

```
<span></span>```
pip<span class="w"> </span>install<span class="w"> </span>gradio><span class="o">=</span><span class="m">5</span>.9.0
python/uv-run<span class="w"> </span>-m<span class="w"> </span>pydantic_ai_examples.weather_agent_gradio

```
```

UI Code
-------

pydantic\_ai\_examples/weather\_agent\_gradio.py```
<span></span>```
<span class="ch">#! pydantic_ai_examples/weather_agent_gradio.py</span>

```
```