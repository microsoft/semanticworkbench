# Evaluation
This is a work-in-progress tool for evaluating Semantic Workbench Assistants for quality.


## Automation and Data Generation
There is currently one part to this which is automation to populate a Workbench conversation automatically without human intervention.
This is implemented using a specialized version of the guided conversation engine (GCE).
The GCE here focuses on the agenda and using an exact resource constraint to force the GCE to have a long running conversation.

There is also a quick `generate_scenario.py` script that can be used to generate new scenarios based on your existing configuration.

### Setup

1. Run the workbench service running locally (at http://127.0.0.1:3000), an assistant service, and create the assistant you want to test.
2. Have LLM provider configured (if you have an assistant running this should be all set). If not, check [pydantic_ai_utils.py](./pydantic_ai_utils.py) for an example of it is configured.
3. Create a configuration file. See [evaluation_config.yaml](evaluation_config.yaml) for an example.
   1. The scenarios field is a list that allows you to specify multiple test scenarios (different conversation paths).

### Run

Use this command to run with a custom configuration file and a specific scenario in that file:

```bash
python gce_simulation.py --config path/to/custom_config.yaml --scenario-idx 0
```

Run the generate script to generate a new scenario based on the current configuration:

```bash
python generate_scenario.py --config path/to/custom_config.yaml
```
