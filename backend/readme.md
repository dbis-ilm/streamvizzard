# StreamVizzard Backend


## Manual Installation

Requires: Python >=3.11,<3.12

```
poetry install
```

The backend can be started by executing the [main.py](src/main.py).

## Configuration

Various settings and functionalities can be adjusted in the [config.py](src/config.py) file.

## CLI

A CLI tool can be accessed in [cli.py](src/cli.py).

For docker setups, the cli can be reached with docker exec -it svbackend svcli

| Command       | Description                                                  | Parameter                                                                            |
|---------------|--------------------------------------------------------------|--------------------------------------------------------------------------------------|
| startPipeline | Executes a given pipeline                                    | **path** to pipeline save file<br>*See additional options in help command*           |
| stopPipeline  | Stops the currently running pipeline                         | -                                                                                    |
| analyzeCostModels | Calculates costModel for the defined operator configurations | **storagePath** to store the calculated costModels and operator execution recordings |
