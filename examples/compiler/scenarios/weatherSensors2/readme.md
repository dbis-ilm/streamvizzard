# Smart City Weather Correlation Analysis

This scenario utilizes weather and particulate matter data from sensor devices across the city of Ilmenau and performs
a correlation analysis between the recorded temperature and matter values.

This scenarios uses the createDataset.py and prepared weatherData.json dataset from the `weatherSensors` scenario.

## Content

1) `origParticulateMatterData.json` Example data from one of the deployed sensor devices to simulate the real-time retrieval of sensor data
2) `streamVizzardPipeline.json`: StreamVizzard pipeline save file to be loaded from the Webinterface
3) `generatedFlink.py`: Example generated analytical Flink sub-pipeline file to be executed on a Flink cluster
4) `expertFlink.py`: The manually created pipeline by an expert user to be executed on a Flink cluster
5) `output_flink_3para.txt`: Example data sink output file for an execution of the Flink pipeline with a parallelism of 3

Please note that the example output files only contain data of the first few seconds of execution due to git size considerations.
For more representative performance results, the pipeline should be executed for a longer duration to mitigate pipeline warmup effects.

## Data Preparation

Execute the `createDataSet.py` setup script which will create a dataset of 200K tuples (~40MB) by default.
Each tuple contains a single measurement of the sensor particulate matter data.
