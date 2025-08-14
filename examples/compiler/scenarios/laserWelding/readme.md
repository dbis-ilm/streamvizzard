# Laser-Welding

[Requires installation of examples operators in StreamVizzard docker-compose]

This scenario performs the automatic detection and prediction of laser beam butt welding (see [publication](https://www.sciencedirect.com/science/article/pii/S266633092500024X?via%3Dihub)) based on long-wave infrared camera (LWIR) and inductive probes sensor data.  

The utilized data is available [here](https://www.sciencedirect.com/science/article/pii/S2352340925001131) and contains recordings for various runs of the laser-welding process.

To simulate a live-execution of the laser-welding process, this scenario utilizes a `Textfile source` to ingest the inductive probes sensor data into the pipeline. 
The recorded LWIR image data is ingested using a `Read Folder source`, which reads and subsequently loads all images within a specified folder.

## Content

1) `prepareData.py` Setup script to prepare the data downloaded above
2) `streamVizzardPipeline.json`: StreamVizzard pipeline save file to be loaded from the Webinterface
3) `cnn.hdf5` and `lstm.hdf5`: Trained neuronal networks for the weld prediction
4) `generatedFlink.py`: Example generated Flink sub-pipeline file to be executed on a Flink cluster
5) `generatedSv.py`: Example generated StreamVizzard sub-pipeline file to be executed on the StreamVizzard engine
6) `output_sv.txt`: Example data sink output file for an execution of the StreamVizzard pipeline
7) `output_flink_5para.txt`: Example data sink output file for an execution of the Flink pipeline with a parallelism of 5

## Data Preparation

After downloading the dataset from above, the data needs to be prepared for the processing within the pipeline.

Execute the `prepareData.py` script (requires OpenCV library) with the path to the raw LWIR and Inductive Probes data of one of the recorded runs. 
For instance: _dataset/Raw/LWIR/001-000_ and _dataset/Raw/Inductive_Probes/001/001-000.csv_

The result is a _sensorData.txt_ file which contains input data for the `sensor` data source operator and a _LWIR_ folder with images as an input for the `camera` data source operator.

## Pipeline Preparation

Before executing the pipeline, the data paths for the two data sources as well as the model paths for the CNN and LSTM operator must be adapted.
For a StreamVizzard docker setup, all files must be available for the container, e.g. by moving them to the configured volume mount location and addressing them in the pipeline relative to _/home/streamvizzard/_.

The same argumentation applies to a subsequent Flink execution. 

However, please note, that Flink does not support a `Read Folder` data source.
To still execute the computational demanding LSTM operator on Flink in a distributed way, the image processing part of the pipeline can remain on the StreamVizzard environment during the execution target configuration.
This will result in two distinct generated pipelines (Flink and StreamVizzard) with an established Kafka data connector (topic: _my-topic2_) to send the results of the StreamVizzard CNN operator to the Flink sub-pipeline.

## Pipeline Execution

Please follow the instructions in the main [readme](../../readme.md) and replace the steps 3-4 of the **Pipeline Execution** section with the subsequent steps.
For the initial run, the topic _my-topic2_ must be created according to the previous steps.

1) Start the generated or provided Flink sub-pipeline to receive input sensor data from the Kafka producer and LWIR-related input data from the StreamVizzard sub-pipeline
2) Load and start the generated or provided StreamVizzard sub-pipeline from the editor to load LWIR images from the created folder and send processed result data to the Flink sub-pipeline.
The `Pipeline -> Visibility -> Auto Arrange` feature can be used to re-arrange generated StreamVizzard pipelines.
For best execution performance, the monitoring feature should be disabled by unchecking `Settings -> Monitor -> Enabled`.
3) Start the Kafka producer (topic: _my-topic_) to publish sensor data from the created _sensorData.txt_ file to the Flink sub-pipeline