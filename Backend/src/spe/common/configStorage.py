import json
import os
from pathlib import Path
from typing import Optional, List, Dict

from streamVizzard import StreamVizzard


class ConfigStorage:
    # ------------ Pipeline Storage ------------

    @staticmethod
    def storePipeline(name: str, data: str) -> bool:
        path = ConfigStorage._retrievePipelineStoragePath()

        try:
            with open(os.path.join(path, name + ".json"), "w", encoding="utf-8") as f:
                f.write(data)

            return True
        except IOError:
            return False

    @staticmethod
    def listStoredPipelines() -> List[str]:
        path = ConfigStorage._retrievePipelineStoragePath()

        res = []

        try:
            files = sorted(Path(path).iterdir(), key=os.path.getmtime, reverse=True)

            for file in files:
                if file.is_file() and file.name.endswith('.json'):
                    fileName = file.stem

                    res.append(fileName)

        except IOError:
            ...

        return res

    @staticmethod
    def loadStoredPipeline(name: str) -> Optional[str]:
        path = ConfigStorage._retrievePipelineStoragePath()

        try:
            with open(os.path.join(path, name + ".json"), "r", encoding="utf-8") as f:
                return f.read()
        except IOError:
            return None

    @staticmethod
    def deleteStoredPipeline(name: str) -> Optional[bool]:
        path = ConfigStorage._retrievePipelineStoragePath()

        filePath = os.path.join(path, name + ".json")

        try:
            if os.path.exists(filePath):
                os.remove(filePath)

                return True
            else:
                return False
        except IOError:
            return None

    @staticmethod
    def _retrievePipelineStoragePath():
        return StreamVizzard.requestOutFolder("storage", "pipelines")

    # ------------ Operator Storage ------------

    @staticmethod
    def storeOperator(data: Dict) -> bool:
        path = ConfigStorage._retrieveOperatorStoragePath()

        # We support handling of different files during deletion/loading, but we currently only use one storage file

        storagePath = os.path.join(path, "storage.json")

        try:
            fileContent = []

            # Load previous content of file

            if os.path.exists(storagePath):
                with open(storagePath, "r", encoding="utf-8") as f:
                    content = json.loads(f.read())
                    fileContent.extend(content)

            # Check if entry exists and update

            for idx in range(len(fileContent) - 1, -1, -1):
                if fileContent[idx]["name"] == data["name"]:
                    fileContent.pop(idx)

            fileContent.insert(0, data)  # Prepend since most recently updated

            # Store data

            with open(storagePath, "w", encoding="utf-8") as f:
                f.write(json.dumps(fileContent))

            return True
        except IOError:
            return False

    @staticmethod
    def deleteStoredOperator(name: str) -> Optional[bool]:
        path = ConfigStorage._retrieveOperatorStoragePath()

        removed = False

        try:
            files = sorted(Path(path).iterdir(), key=os.path.getmtime, reverse=True)

            for file in files:
                updatedContent = None

                # Search file if this contains our operator preset

                with file.open("r", encoding="utf-8") as f:
                    content = json.loads(f.read())

                    for idx in range(len(content) - 1, -1, -1):
                        if content[idx]["name"] == name:
                            content.pop(idx)

                            updatedContent = content

                # If found, modify or delete file

                if updatedContent is not None:
                    if len(updatedContent) > 0:
                        with file.open("w", encoding="utf-8") as f:
                            f.write(json.dumps(updatedContent))
                    else:
                        os.remove(file)

                    removed = True

        except IOError:
            return None

        return removed

    @staticmethod
    def listStoredOperators() -> List[str]:
        path = ConfigStorage._retrieveOperatorStoragePath()

        res = []

        try:
            files = sorted(Path(path).iterdir(), key=os.path.getmtime, reverse=True)

            for file in files:
                with file.open("r", encoding="utf-8") as f:
                    content = json.loads(f.read())

                    res.extend(content)

        except IOError:
            ...

        return res

    @staticmethod
    def _retrieveOperatorStoragePath():
        return StreamVizzard.requestOutFolder("storage", "operators")
