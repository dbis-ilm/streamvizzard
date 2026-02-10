# Energy Market Analytics

This scenario utilizes energy market data taken from the [German Federal Network Agency](https://www.smard.de/en) and performs data analytical and aggregating operations on high-frequence input data.

## Content

1) `createDataSet.py` Setup script to download and prepare the energy marked data
2) `streamVizzardPipeline.json`: StreamVizzard pipeline save file to be loaded from the Webinterface
3) `generatedFlink.py`: Example generated Flink pipeline file to be executed on a Flink cluster
4) `expertFlink.py`: The manually created pipeline by an expert user to be executed on a Flink cluster
5) `output_flink_8para.txt`: Example data sink output file for an execution of the Flink pipeline with a parallelism of 8

Please note that the example output files only contain data of the first few seconds of execution due to git size considerations.
For more representative performance results, the pipeline should be executed for a longer duration to mitigate pipeline warmup effects.

## Data Preparation

Execute the `createDataSet.py` setup script which will create a dataset of 1M tuples (~130MB) by default.
Each tuple contains a time-series array of energy market data.
Various parameters may be specified to adjust the size and characteristics of the dataset.

## Execution

To fully utilize Flinks distributed execution performance, the Kafka topic should be partitioned according to the 
selected parallelism of the pipeline (in this case 8).