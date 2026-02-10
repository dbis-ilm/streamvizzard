# Smart City Weather Analytics

This scenario utilizes weather data from sensor devices across the city of Ilmenau and performs various analytical 
operations, such as calculating statistics and detecting sensors whose statistics deviates from the global mean.

This scenario showcases the heterogeneous deployment of the initial pipeline across the cloud and edge layer and 
distributes the initial pipeline into a StreamVizzard sub-pipeline to be executed on various sensor edge devices and 
a Flink sub-pipeline to be executed on a central cluster.

## Content

1) `createDataSet.py` Setup script to prepare the weather data set based on the provided historic recordings
2) `origWeatherData.json` Example data from one of the deployed sensor devices to simulate the real-time retrieval of sensor data
3) `streamVizzardPipeline.json`: StreamVizzard pipeline save file to be loaded from the Webinterface
4) `generatedFlink.py`: Example generated analytical Flink sub-pipeline file to be executed on a Flink cluster
5) `generatedSv.py`: Example generated StreamVizzard sub-pipeline which simulates the actual sensor application on the edge devices
6) `expertFlink.py`: The manually created pipeline by an expert user to be executed on a Flink cluster
7) `output_flink_1para.txt`: Example data sink output file for an execution of the Flink pipeline with a parallelism of 1

Please note that the example output files only contain data of the first few seconds of execution due to git size considerations.
For more representative performance results, the pipeline should be executed for a longer duration to mitigate pipeline warmup effects.

## Data Preparation

Execute the `createDataSet.py` setup script which will create a dataset of 200K tuples (~85MB) by default.
Each tuple contains a single measurement of sensor weather data.
For each utilized sensor, a different sensorID should be specified as a parameter.
Various parameters may be specified to adjust the size and characteristics of the dataset.

## Execution

For each simulated sensor 'device', a separate instance of the StreamVizzard engine should be executed with dedicated dataset to produce output data for the central Flink cluster.

Please note: Due to the limitations of the internal StreamVizzard execution engine, each sensor is limited in its achievable data throughput (~up to 1K tup/s). 
To mitigate this, several StreamVizzard instances should be utilized to simulate a high data input rate for the Flink cluster.