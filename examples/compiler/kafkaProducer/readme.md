# Example Kafka Producer

Produces data tuples to a configured Kafka broker based on an input data file (one data tuple per line-by-line).

See the [docker-compose](docker-compose.yml) file for further configuration parameters, such as the Kafka broker and topic.

To access input file within the Kafka container at _/data/_, the volume mount must be specified in the compose file.