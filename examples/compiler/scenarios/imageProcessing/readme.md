# Image Processing Analysis

This scenario utilizes the [Stanford Dogs dataset](http://vision.stanford.edu/aditya86/ImageNetDogs/main.html) as sample image data for various real-time analytics.

Moreover, it showcases the heterogeneous deployment of the initial pipeline across the cloud and edge layer and 
distributes the initial pipeline into a StreamVizzard sub-pipeline to be executed on an image recording sensor edge device and 
a Flink sub-pipeline to be executed on a central cluster.

## Content

1) `streamVizzardPipeline.json`: StreamVizzard pipeline save file to be loaded from the Webinterface
2) `generatedFlink.py`: Example generated analytical Flink sub-pipeline file to be executed on a Flink cluster
3) `generatedSv.py`: Example generated StreamVizzard sub-pipeline which simulates the actual sensor application on the edge device
4) `expertFlink.py`: The manually created pipeline by an expert user to be executed on a Flink cluster
5) `output_flink_3para.txt`: Example data sink output file for an execution of the Flink pipeline with a parallelism of 3

Please note that the example output files only contain data of the first few seconds of execution due to git size considerations.
For more representative performance results, the pipeline should be executed for a longer duration to mitigate pipeline warmup effects.

## Data Preparation

Download the image dataset and adjust the path to access the files from the StreamVizzard docker container, which simulates the sensor edge device application.