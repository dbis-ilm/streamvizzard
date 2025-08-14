from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Type, Tuple, Optional
import logging
import os
import shutil
import traceback

from spe.pipeline.operators.operatorDB import getPathByOperator

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator


def emptyFolder(folderPath: str):
    try:
        for item in os.listdir(folderPath):
            item_path = os.path.join(folderPath, item)

            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)  # Remove files or symbolic links
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Remove directories
    except:
        logging.log(logging.ERROR, traceback.format_exc())


def getStructuredOperatorPath(op: Type[Operator], rootFolder: Optional[str] = None,
                              mkdirs: bool = True) -> Tuple[str, str]:
    """ Creates a structured folder skeleton according do the full operator path, e.g. module1/folder1/
    Returns parent folder, name of operator file (without extension) """

    fullPath = Path(getPathByOperator(op))
    opName = fullPath.parts[len(fullPath.parts) - 1]  # Last element of path

    parentFolder = fullPath.parent

    if rootFolder is not None:
        parentFolder = os.path.join(rootFolder, parentFolder)

    if mkdirs:
        os.makedirs(parentFolder, exist_ok=True)

    return str(parentFolder), opName
