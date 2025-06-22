
## For now

* Refactor to this folder strcuture
* do not change any code or contracts


analysis/
├── __init__.py
├── processor.py            # ← orchestrator module, clearly top-level
├── analyzer_config.py
├── metrics_aggregator.py
└── processors/             # ← clearly supporting, modular processors
    ├── __init__.py
    ├── health_data.py
    ├── hevy.py
    ├── oura.py
    ├── whoop.py
    └── withings.py


Make a folder structure like this

## For later

* Separate out aggregators
* do something with workout data that is working now