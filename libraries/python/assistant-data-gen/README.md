# Data Generation

This is a tool for generating data for testing Semantic Workbench assistants.

The core functionality of this library is an automation to populate a Workbench conversation automatically without human intervention.
This is implemented using a specialized version of the guided conversation engine (GCE).
The GCE here focuses on the agenda and using an exact resource constraint to force the GCE to have a long running conversation.

There is also a quick `generate_scenario.py` script that can be used to generate new scenarios based on your existing configuration.

### Setup

1. Run the workbench service running locally (at http://127.0.0.1:3000), an assistant service, and create the assistant you want to test.
2. Have LLM provider configured. Check [pydantic_ai_utils.py](./assistant_data_gen/pydantic_ai_utils.py) for an example of how it is configured for Pydantic AI.
   1. For example, create a `.env` file with your Azure OpenAI endpoint set as `ASSISTANT__AZURE_OPENAI_ENDPOINT=<your_endpoint>`
3. Create a configuration file. See [document_assistant_example_config.yaml](./configs/document_assistant_example_config.yaml) for an example.
   1. The scenarios field is a list that allows you to specify multiple test scenarios (different conversation paths).

### Run

Use this command to run with a custom configuration file and a specific scenario in that file:

```bash
python scripts/gce_simulation.py --config path/to/custom_config.yaml --scenario-idx 0
```

Run the generate script to generate a new scenario based on the current configuration:

```bash
python scripts/generate_scenario.py --config path/to/custom_config.yaml
```

### Recommendations
1. Be as specific as possible with your conversation flows. Generic conversation flows and/or resource constraints that are too high can lead to the agents getting stuck in a thank you loop.
