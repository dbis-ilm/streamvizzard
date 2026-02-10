import os
import random

import argparse
import json
import sys

import requests
from datetime import datetime

from typing import Callable, List, Dict, Tuple, Optional


"""
Prepares a dummy data set based on real recorded weather sensor data from the city of Ilmenau, Germany.
"""


def loadInputData(file):
    with open(file, "r") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputFile', type=str, default="origWeatherData.json", required=False, help="The input file including extension.")
    parser.add_argument('--targetTuples', type=int, default=200000, required=False, help="The amount of tuples in the output file.")
    parser.add_argument('--outputFile', type=str, default="weatherData.json", required=False, help="The output file including extension.")
    parser.add_argument('--sensorID', type=int, default=1, required=False, help="The artificial sensorID to add to the dataset.")

    args = parser.parse_args()

    inputFile = args.inputFile
    targetTuples = args.targetTuples
    outputFile = args.outputFile
    sensorID = args.sensorID

    data = loadInputData(inputFile)

    if data is None:
        print("Error loading data!")

        return

    res: List[str] = []

    # Duplicate data until target tuple count is reached

    while len(res) < targetTuples:
        for d in data:
            d["sensorID"] = sensorID
            res.append(json.dumps(d) + "\n")

            if len(res) == targetTuples:
                break

    # Write data

    with open(outputFile, "w") as f:
        f.writelines(res)


if __name__ == "__main__":
    main()
