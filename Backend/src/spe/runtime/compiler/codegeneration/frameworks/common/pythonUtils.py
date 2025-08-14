import ast
import pkgutil
import sys
import sysconfig
from importlib import metadata
from importlib.metadata import distributions
from typing import List


# ------------------------------------------------ Dependency Extraction -----------------------------------------------

def extractDependencyList(importList: List[str]):
    """ Retrieves a list of installable dependencies with versions based on a list of imports. """

    # Add built-in module names
    builtins = set(sys.builtin_module_names)

    # Add standard library modules
    stdlib = [name for _, name, _ in pkgutil.iter_modules([sysconfig.get_path('stdlib')])]

    topLevelModules = _extractTopLevelModules(importList)

    # Unique result set
    foundDependencies = set()

    for mod in topLevelModules:
        if mod not in builtins and mod not in stdlib:
            pyPiPackage = pyPiPackageMapping.get(mod, mod)
            packageName, packageVersion = _getPackageVersion(pyPiPackage)

            if packageName is not None and packageVersion is not None:
                foundDependencies.add(f"{packageName}=={packageVersion}")
            else:
                foundDependencies.add(mod)

    return foundDependencies


def _getPackageVersion(module):
    try:
        dist = metadata.distribution(module)
        name = dist.metadata['Name']
        return name, dist.version
    except metadata.PackageNotFoundError:
        # Module might be part of another dist or not installed
        return None, None


def _extractTopLevelModules(importList):
    # Join lines into one code block and parse it
    tree = ast.parse("\n".join(importList))

    modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split('.')[0])
    return modules


def _buildPyPiMapping():
    mapping = {}
    for dist in distributions():
        try:
            top_levels = dist.read_text('top_level.txt')
            if top_levels:
                for top_level in top_levels.splitlines():
                    mapping[top_level] = dist.metadata['Name']
        except Exception:
            continue
    return mapping


pyPiPackageMapping = _buildPyPiMapping()


# ----------------------------------------------------------------------------------------------------------------------
