# StreamVizzard v0.8

StreamVizzard ist an interactive and explorative stream processing editor written in python.

## Core Components

### Dynamic Stream Processing Engine

StreamVizzard comes with its custom python stream processing engine that 
was designed to allow instantaneous runtime modifications without the need to restart the pipeline.

### Adaptive Visualizer

The adaptive visualizer allows to explore the processed data by displaying the data
each operator processed as well as various different statistics.

### Time Traveling Debugger

The integrated debugger allows to explore the execution history of the pipeline and travel back
to any previous state in the execution to review the pipeline behavior.

## Project Structure

StreamVizzard is divided into a [Webinterface](Frontend/readme.md), that is responsible for user interaction
and visualization, and a [Backend](Backend/readme.md), that brings its own custom stream processing engine
for execution and modification of the pipeline.

## Installation

Both modules must be installed and executed separately according to the installation instructions provided in their respective readme files.

## Docker

A Docker image for easy deployment of the entire system will be available soon.



## Publications

- Timo Räth, Kai-Uwe Sattler: [StreamVizzard: An Interactive and Explorative Stream Processing Editor](https://dl.acm.org/doi/pdf/10.1145/3524860.3543283), DEBS 2022

- Timo Räth, Kai-Uwe Sattler: [Interactive and Explorative Stream Processing](https://dl.acm.org/doi/pdf/10.1145/3524860.3543287), DEBS 2022

- Timo Räth, Kai-Uwe Sattler: [Traveling Back in Time: A Visual Debugger for Stream Processing Applications](https://ieeexplore.ieee.org/document/10184546), ICDE 2023

- Timo Räth, Ngozichukwuka Onah, Kai-Uwe Sattler: [Interactive Data Cleaning for Real-Time Streaming Applications](https://dl.acm.org/doi/pdf/10.1145/3597465.3605229), HILDA 2023

- Timo Räth, Francesco Bedini, Kai-Uwe Sattler, Armin Zimmermann: [Demo: Interactive Performance Exploration of Stream Processing Applications Using Colored Petri Nets](https://dl.acm.org/doi/10.1145/3583678.3603280), DEBS 2023