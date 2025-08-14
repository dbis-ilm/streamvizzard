# Compiler / Pipeline Generator - Tutorial & Evaluation

This file contains detailed step-by-step instructions to execute and evaluate the pipeline generator for various example data processing scenarios, targeting Apache Flink as the execution environment.

In addition, Flink and Kafka docker files are provided to quickly start a custom Flink cluster with configured Kafka broker to validate the execution of the generated pipeline files.

For convenience, the scenario subfolders contain example output files of the pipeline generation process and the Flink execution, to quickly review the produced results and execute the evaluation.
These output files may also be produced by following the described tutorial steps below.

## Tutorial

### Data Preparation

Prepare the required datasets based on the instructions in the respective data processing scenario subfolders.

### StreamVizzard Preparations

Startup the StreamVizzard system and load the pipeline save file in the Frontend interface `Pipeline -> Load`.

The example pipelines in the StreamVizzard system reflect the pipeline prototype representations during the development stage and contain Textfile data sources, to quickly execute and validate the constructed pipelines.
This prototype operators may be replaced by deployment-oriented data sources, such as Apache Kafka, later on.

Adapt the file paths of the respective operators, such as the data sources, to match the provided files of the example scenarios.
For a docker setup, the files must be moved to the volume mount to be accessible in _/home/streamvizzard/
_ for the container.

To allow the system to suggest reasonable execution targets for the operators in the pipeline during the generation process, the pipeline should be first executed to collect execution statistics.
Activate `Settings -> Monitor -> Track Stats` and execute the pipeline. 
For most reliable results, the data sources should produce data with the highest possible rate. 
Moreover, a longer pipeline execution duration reduces the impact of execution fluctuations.

After the collection of execution stats, the pipeline generation process can be started. To generate deployment-oriented result pipelines, the Textfile data sources can be replaced by Kafka sources while preserving the recorded execution statistics.
If desired, right-click on the Textfile sources and choose `Replace -> Base -> Sources -> Kafka Source`. 
Adapt the Kafka settings, if required.

Please note: Depending on the subsequent execution environment, all file paths within the pipeline (data sources, data sinks, ...) might need to be adapted - either before the generation within the editor or after the generation within the generated pipeline files.
When utilizing the subsequently described Flink docker cluster setup, all file paths should relate to _/home/pyflink/_.

### Pipeline Compiler

Open the Pipeline Compiler `Pipeline -> Compile`. Various settings, such as the operator placement algorithm or the placement weights may be adjusted to individually configure the execution target suggestion process.

Start the target suggestion process with `Analyze` and review the proposed execution targets of each operator.
At this point, the proposed execution targets may be exchanged, execution characteristics of the operators adjusted, or placement weights modified to adapt the proposed pipeline configuration.
One of the most important settings are the requested throughputs of the data sources, which allows to adjust the expected pipeline input data rates during the deployment.

The suggested execution targets highly depend on the provided operator information, such as the execution statistics, which depend on the system the StreamVizzard pipeline was executed on.
For comparable results, the StreamVizzard pipeline should be executed on the same system as the subsequent Flink execution.
However, additional, more precise information may be provided manually or extracted from cost models.

After suitable configurations have been determined, `Compile` the pipeline and review the produced output files. For a docker setup, the volume mounts can be utilized to access the out files of the StreamVizzard system.

### Flink Execution

To execute the generated pipeline files on Apache Flink, a running Flink cluster and potentially a separate Kafka broker must be provided.

#### Flink & Kafka Setup

The provided example [docker-compose](flinkCluster/docker-compose.yml) file contains instructions to automatically set up a separate Flink cluster with installed Python libraries and a Kafka broker.
Make sure to adjust the volume mounts to access the internal file system of the Flink container at _/home/pyflink/_.

The Kafka broker is configured to be accessible at _localhost:9092_ from outside the docker network (e.g. host machine) and at _kafka:9093_ from inside the docker (e.g. StreamVizzard & Flink pipeline).
Adjust the broker settings in the StreamVizzard or Flink pipeline accordingly.

#### Kafka Producer

For convenience, a further [docker-compose](kafkaProducer/docker-compose.yml) file is provided, which allows to start an example Kafka data producer to ingest data tuples based on an input data file.
This producer can be utilized to validate the generated Flink pipelines which rely on input data from a Kafka data source.

Make sure to adjust the producer settings, such as the Kafka topic name and the path of the input data file in the respective compose file.

Please note, the Kafka topic must exist before the Flink pipeline is started, since the topic meta-data is requested on startup.
To initially create the required topics run: 

`docker exec kafka /opt/kafka/bin/kafka-topics.sh --create --topic my-topic --bootstrap-server localhost:9092`

#### Pipeline Execution

1) Move the generated Flink _pipeline.py_ (or provided _generatedFlink.py_) file to the specified Flink mount location to allow the jobmanager to access it at _/home/pyflink/_.

2) Download the [flink-sql-connector-kafka.jar](https://mvnrepository.com/artifact/org.apache.flink/flink-sql-connector-kafka/3.4.0-1.20) file, 
which is required for accessing the Kafka data source in Flink, and also move it to the Flink mount location.

3) Execute the Flink job with: 

`docker exec pfjobmanager ./bin/flink run -py /home/pyflink/pipeline.py --jarfile /home/pyflink/flink-sql-connector-kafka-3.4.0-1.20.jar`

4) [Optional] If a Kafka data source is included in the pipeline, start the separate Kafka data producer after the Flink job has completed its startup.

5) Monitor the Flink execution in the Flink Webinterface (default: http://localhost:8085). 
Due to the unbound Kafka data source, the job must be cancelled manually after the desired execution duration has elapsed.

The result output files of the data sinks can be accessed at the specified volume mount location. 
By default, the output files are split into part files, which might be hidden (starting with ".") due to the cancellation of the Flink job.
For the evaluation, all part files must be merged into a single result file.

To produce a single output file during the job execution, the _FileSink_ definition in the generated Flink pipeline can be extended by
`.with_rolling_policy(RollingPolicy.default_rolling_policy(9999999, 9999999, 9999999))`

### Evaluation

To evaluate and visualize the achieved throughput and the semantic correctness of the generated Flink pipelines during execution, 
the provided [evaluation script](flinkTpEval.py) (requires matplotlib) can be utilized. 
The evaluation script requires the generated output files of the pipeline data sinks to access the timestamps and the values of the produced data tuples.

By providing both the output files of the StreamVizzard and Flink execution, the script allows to compare the achieved throughputs and to verify the semantic correctness of the generated pipelines.
Please note, that the pipelines should receive the same input data in order to verify the same produced output values.
The Kafka producer should therefore only start when the Flink job is running and ready to receive input data.

For most representative results, the pipelines should be executed for a suitable amount of time to reduce the impact of pipeline warmup effects.
Moreover, for comparable performance results, the data sources in the StreamVizzard pipeline should feature the same rates as during the Flink execution.

To quickly execute the evaluation, the provided example StreamVizzard _output_sv.txt_ and Flink _output_flink_5para.txt_ output files in the scenario sub-folders can be employed.

Depending on the utilized data scenario, the sliding window size might need to be adapted for reasonable results.
