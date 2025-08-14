# Example Flink Cluster & Kafka Broker

The provided [docker-compose](docker-compose.yml) file starts a standalone Flink cluster in cluster mode with a configurable number of taskmanager (see parameter `scale` in taskmanager service definition).

In addition, a separate Kafka broker is started in KRaft mode.

Please note: Both this docker container as well as the StreamVizzard container share the same docker network to allow communication between the container.

The Kafka broker is configured to be accessible at _localhost:9092_ from outside the docker network (host machine) and at _kafka:9093_ from inside the docker, such as from a running Flink or StreamVizzard (docker) pipeline.

Please adapt the specified Flink volume mounts to allow the jobmananger and taskmanagers to access files during the job execution. 
Depending on the available system resources, adjustments of the memory settings might be required.

A Flink job can be scheduled by executing:

`docker exec pfjobmanager ./bin/flink run -py /home/pyflink/{pipelineFile}.py`
