import os
import sys
from pathlib import Path

import cv2

dataPathLWIR: str = "dataset/Raw/LWIR/001-000"
dataPathInductiveProbes: str = "dataset/Raw/Inductive_Probes/001/001-000.csv"

duplication = 4  # How many times the data should be duplicated to increase the processing duration for the pipeline


def readFile(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

        return None


def prepareData():
    # Inductive data preparation

    inductive = readFile(dataPathInductiveProbes)

    if inductive is None:
        sys.exit(-1)

    inductive.pop(0)  # Skip header line

    # Downsample
    step = len(inductive) / 8720
    indices = [int(i * step) for i in range(8720)]
    inductive = [inductive[i] for i in indices]

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sensorData.txt"), "w") as f:
        for dup in range(duplication):
            for idx, elm in enumerate(inductive):
                sub = elm.split(",")

                data = ""

                if idx > 0 or dup > 0:
                    data += "\n"

                data += f"[{sub[2]},{sub[3]},{sub[4].strip()}]"

                f.write(data)

    # LWIR data preparation

    outFolder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LWIR")

    if not os.path.exists(outFolder):
        os.mkdir(outFolder)

    targetSize = (9, 59)

    files = sorted(Path(dataPathLWIR).iterdir())

    for dup in range(duplication):
        for f in files:
            img = cv2.imread(f, cv2.IMREAD_UNCHANGED)

            h, w = img.shape[:2]

            startX = max((w - targetSize[0]) // 2, 0)
            endX = startX + min(targetSize[0], w)

            newImg = img[0:h, startX:endX]

            newImg = cv2.resize(newImg, targetSize, interpolation=cv2.INTER_AREA)

            cv2.imwrite(os.path.join(outFolder, str(dup) + "_" + os.path.basename(f)), newImg)


if __name__ == "__main__":
    prepareData()
