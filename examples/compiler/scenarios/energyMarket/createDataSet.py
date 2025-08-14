import os
import random

import argparse
import json
import requests
from datetime import datetime

from typing import Callable, List, Dict, Tuple, Optional


"""
Fetches energy market data from the SMARD (https://www.smard.de) webpage and generates a file that contains data tuples
with a timestamp and a time-series of energy market data to be used as an input for a stream processing pipeline.
"""


def fetchData() -> Optional[List]:
    dateString = "2024-01-01 00:00:00"
    dateObj = datetime.strptime(dateString, "%Y-%m-%d %H:%M:%S")
    epoch = int(dateObj.timestamp() * 1000)

    url = f"https://www.smard.de/app/chart_data/4169/DE/4169_DE_hour_{epoch}.json"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to fetch data: {response.status_code}")

        return None

    data = response.json()

    if "series" not in data or not data["series"]:
        print("No data available for the specified date.")

        return None

    return data["series"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--targetTuples', type=int, default=200000, required=False, help="The amount of tuples in the output file.")
    parser.add_argument('--timeSeriesLength', type=int, default=80, required=False, help="How many elements should be present inside the time-series per tuple.")
    parser.add_argument('--outputFile', type=str, default="energyData.json", required=False, help="The output file including extension.")
    parser.add_argument('--outlierChance', type=float, default=0.15, required=False, help="The chance for adding a tuple as an outlier.")
    parser.add_argument('--missingValueChance', type=float, default=0.15, required=False, help="The chance to insert a null value for each tuple.")

    args = parser.parse_args()

    targetTuples = args.targetTuples
    timeSeriesLength = args.timeSeriesLength
    outlierChance = args.outlierChance
    missingValueChance = args.missingValueChance
    outputFile = args.outputFile

    data = fetchData()

    if data is None:
        print("Error fetching data!")

        return

    res: List[str] = []

    # Duplicate data until target tuple count is reached

    while len(res) < targetTuples:
        for d in data:
            time = d[0]

            timeSeries = []

            try:
                price = float(d[1])

                for i in range(timeSeriesLength):
                    # Create artificial time-series value based on original price

                    tsPrice = price * random.uniform(0.8, 1.2)

                    # Add outlier/missing values to data

                    if random.random() < outlierChance:
                        tsPrice *= 100
                    elif random.random() < missingValueChance:
                        tsPrice = None

                    timeSeries.append(tsPrice)
            except Exception:
                pass

            res.append(json.dumps({"time": time, "prices": timeSeries}) + "\n")

            if len(res) == targetTuples:
                break

    # Write data

    with open(outputFile, "w") as f:
        f.writelines(res)


if __name__ == "__main__":
    main()
