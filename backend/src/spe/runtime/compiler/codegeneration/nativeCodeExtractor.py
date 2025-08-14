from __future__ import annotations
import ast
import importlib
import inspect
import os
import textwrap
import types
from _ast import Module
from typing import TYPE_CHECKING, Optional, List, Union, Dict, Any

from spe.common.tuple import Tuple
from streamVizzard import StreamVizzard
from utils.utils import printWarning

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator


# TODO: Handle subFunctions/classes outside our targetAST (class methods) [but in same file] or from outside (Utils method - onError...)
#       Might occur when extracting custom data types or when extraction operator code
# TODO: Handle debugging annotations such as if self.isDebuggingEnabled(): ... | Just skip those sections
# Limitation: Internal Class extracts are treated as unique by name -> Do not support same class name in different files

class NativeCodeExtractor:
    class Result:
        def __init__(self, imports: str, code: str, classExtracts: List[ClassExtractor.Result]):
            self.imports = imports
            self.code = code
            self.classExtracts = classExtracts

    def __init__(self, op: Operator):
        self.op = op

        self.fileAst: Optional[Module] = None
        self.targetAst: Optional[Module] = None

    @staticmethod
    def fromClassMethod(op: Operator, targetClass: type, targetFuncName: str) -> Optional[NativeCodeExtractor]:
        extr = NativeCodeExtractor(op)

        extr.fileAst, extr.targetAst = NativeCodeExtractor.getClassMethodAST(targetClass, targetFuncName)

        if extr.fileAst is None or extr.targetAst is None:
            return None

        return extr

    @staticmethod
    def fromRawCode(op: Operator, rawCode: str) -> Optional[NativeCodeExtractor]:
        extr = NativeCodeExtractor(op)

        extr.targetAst = ast.parse(textwrap.dedent(rawCode))

        if extr.targetAst is None:
            return None

        return extr

    def extract(self, allowInternalRefs: bool) -> Optional[Result]:
        """ Extracts the code for the current state of the targetAST and separate into imports and code.
        Also extracts custom classes e.g. DataTypes from the internal SV system. At this point we may
        decide if we allow internal references that also have internal references - in case compiler can override them.
        """

        try:
            # If self references remain (methods or params) the extraction is not possible

            if self.hasSelfReferences():
                return None

            # Extract Imports

            importRes, extractedInternalClasses = self.handleImports(allowInternalRefs)

            if extractedInternalClasses is None:
                return None

            importCode = ast.unparse(importRes.toImportAst(skipInternal=True))

            bodyAST = importRes.targetAst

            bodyCode = ast.unparse(bodyAST)

            return NativeCodeExtractor.Result(importCode, bodyCode, extractedInternalClasses)

        except Exception:
            return None

    def convertParams(self):
        """ Tries to replace all self.[x] params of the node with the actual values of the operator.
        Example: self.abc is replaced with the literal 'test' if 'test' is the current value of that param.
        """

        class ConvertParamTransformer(ast.NodeTransformer):
            def __init__(self, op: Operator):
                self.op = op

            def visit_Attribute(self, n):
                # Check if the attribute is a self attribute
                if isinstance(n.value, ast.Name) and n.value.id == "self":
                    attr_name = n.attr

                    # Replace all self.[attrs] with the value of the attribute from the object

                    if hasattr(self.op, attr_name):
                        attrValue = getattr(self.op, attr_name)

                        astNode = self.valueToAST(attrValue)

                        if astNode is not None:
                            return ast.copy_location(astNode, n)

                return self.generic_visit(n)

            def valueToAST(self, value):
                if isinstance(value, (int, float, str, bool, type(None))):
                    return ast.Constant(value=value)
                elif isinstance(value, list):
                    return ast.List(elts=[self.valueToAST(v) for v in value], ctx=ast.Load())
                elif isinstance(value, tuple):
                    return ast.Tuple(elts=[self.valueToAST(v) for v in value], ctx=ast.Load())
                elif isinstance(value, dict):
                    return ast.Dict(
                        keys=[self.valueToAST(k) for k in value.keys()],
                        values=[self.valueToAST(v) for v in value.values()])
                else:  # Unsupported types like callables
                    return None

        self.targetAst = ConvertParamTransformer(self.op).visit(self.targetAst)

    def renameVar(self, varName: str, newVarName: str):
        """ Renames a variable and all occurrences with a new name. """

        class RenameTransformer(ast.NodeTransformer):
            def visit_Name(self, n):
                if n.id == varName:
                    n.id = newVarName
                return n

        self.targetAst = RenameTransformer().visit(self.targetAst)

    def replaceSVInternals(self):
        """ - Replaces internal access to the "inputTuple.data" with $input
            - Replaces createTuple calls with the actual python tuple object
        """

        # Remove self.createTuple calls with argument (tuple) of the function

        class RemoveCreateTuple(ast.NodeTransformer):
            def __init__(self, op: Operator):
                self.op = op

                self.createTupleName = op.createTuple.__name__

            def visit_Call(self, n):
                # Check if the call is to "self.createTuple"

                if isinstance(n.func, ast.Attribute) and n.func.attr == self.createTupleName and self.isRootSelf(n.func):
                    # Replace the entire call with its first argument
                    if len(n.args) == 1:
                        return n.args[0]

                return self.generic_visit(n)

            @staticmethod
            def isRootSelf(node):
                while isinstance(node, ast.Attribute):
                    node = node.value

                return isinstance(node, ast.Name) and node.id == 'self'

        self.targetAst = RemoveCreateTuple(self.op).visit(self.targetAst)

        # Replace tuple.data calls with $input

        def extractTupleInputName() -> Optional[str]:
            for node in ast.walk(self.targetAst):
                if isinstance(node, ast.FunctionDef):
                    # For each function definition, check its arguments for type 'Tuple'
                    for arg in node.args.args:
                        if (arg.annotation and isinstance(arg.annotation, ast.Name)
                                and arg.annotation.id == Tuple.__name__):
                            return arg.arg  # Return the argument name (e.g., 'tupleIn')

            return None

        tupInputName = extractTupleInputName()

        class ReplaceSVInputTuple(ast.NodeTransformer):
            def visit_Attribute(self, node):
                # Check if the attribute access is on "tupleIn.data"'"
                if isinstance(node.value, ast.Name) and node.value.id == tupInputName and node.attr == "data":
                    # Replace "tupleIn.data" with "$input"
                    return ast.Name(id="$input", ctx=ast.Load())
                return self.generic_visit(node)

        if tupInputName is not None:
            self.targetAst = ReplaceSVInputTuple().visit(self.targetAst)

    def discardFuncSignature(self, funcName: str):
        """ Removes the signature of the function and sets the function body as the new Ast. """
        for node in ast.walk(self.targetAst):
            if isinstance(node, ast.FunctionDef) and node.name == funcName:
                # Return the function body (without the signature)
                self.targetAst = ast.Module(body=node.body)

                return

    def disassemblyReturnTuple(self):
        """ Replaces all return statements on the top level of the code with array access to first element.
        This assumes, that the code returns a tuple in any case! Will not replace return values in nested
        functions inside the code, only on the top level."""

        class TopLevelReturnReplacer(ast.NodeTransformer):
            def __init__(self):
                super().__init__()
                self.nestingLevel = 0

            def visit_FunctionDef(self, node):
                self.nestingLevel += 1
                self.generic_visit(node)
                self.nestingLevel -= 1
                return node

            def visit_AsyncFunctionDef(self, node):
                self.nestingLevel += 1
                self.generic_visit(node)
                self.nestingLevel -= 1
                return node

            def visit_ClassDef(self, node):
                self.nestingLevel += 1
                self.generic_visit(node)
                self.nestingLevel -= 1
                return node

            def visit_Return(self, node):
                if self.nestingLevel == 0 and node.value is not None:
                    if not (isinstance(node.value, ast.Constant) and node.value.value is None):
                        node.value = ast.Subscript(
                            value=node.value,
                            slice=ast.Index(value=ast.Constant(value=0)),
                            ctx=ast.Load()
                        )
                return node

        self.targetAst = TopLevelReturnReplacer().visit(self.targetAst)

    def handleImports(self, allowInternalRefs: bool = True):
        # Extract Imports

        self.fileAst, self.targetAst = ImportExtractor.resolveAliasImports(self.fileAst, self.targetAst)
        importRes = ImportExtractor.extractUsedImports(self.fileAst, self.targetAst, True)

        # Check if we can extract internal imports [Only if those are explicitly mentioned in the code]

        extractedInternalClasses: List[ClassExtractor.Result] = []

        for imp in importRes.importEntries:
            if not imp.internal:
                continue

            # TODO: Might also be methods not only classes that we import here (handle differently!) [and annotate that its no class?]
            classExtract = ClassExtractor(imp.moduleName, imp.filePath).extract(allowInternalRefs)

            if classExtract is None:
                printError(f"Can't extract internal import {imp.moduleName} from {imp.filePath}!")

                return None, None

            extractedInternalClasses.append(classExtract)

        return importRes, extractedInternalClasses

    def hasSelfReferences(self):
        """ Detects any self functions calls or attributes that remain in the code. """

        class SelfAccessDetector(ast.NodeVisitor):
            def __init__(self):
                self.foundSelfAccess = False

            def visit_Attribute(self, n):
                # Check if the attribute is a self attribute [variable or call]
                if isinstance(n.value, ast.Name) and n.value.id == "self":
                    self.foundSelfAccess = True

                self.generic_visit(n)

        analyzer = SelfAccessDetector()
        analyzer.visit(self.targetAst)

        return analyzer.foundSelfAccess

    @staticmethod
    def getClassMethodAST(targetClass: type, targetFuncName: str):
        try:
            with open(inspect.getsourcefile(targetClass), "r") as file:
                opClassContent = file.read()
        except FileNotFoundError:
            printError(f"File not found for class {targetClass}!")

            return None, None

        fileAst = ast.parse(opClassContent)
        targetAst = NativeCodeExtractor.extractMethodAst(fileAst, targetFuncName, False)

        return fileAst, targetAst

    @staticmethod
    def extractMethodAst(fileAst: Module, targetMethodName: str, bodyOnly: bool) -> Optional[Module]:
        for node in ast.walk(fileAst):
            if isinstance(node, ast.FunctionDef) and node.name == targetMethodName:
                returnAst = [node] if not bodyOnly else node.body
                return ast.fix_missing_locations(ast.Module(body=returnAst, type_ignores=[]))

        return None

    @staticmethod
    def extractFunctionName(code: str) -> Optional[str]:
        """ Extracts the name of the function represented within the passed code, such as a = myFuncName(1, 2, 3) """

        codeAST = ast.parse(code)

        class FuncNameExtractor(ast.NodeTransformer):
            def __init__(self):
                self.detectedFuncName = None

            def visit_Call(self, node):
                self.generic_visit(node)

                # Check if it's a method call
                if isinstance(node.func, ast.Attribute):
                    self.detectedFuncName = node.func.attr

                return node

        extractor = FuncNameExtractor()
        extractor.visit(codeAST)

        return extractor.detectedFuncName

    @staticmethod
    def addNamedFunctionAttribute(funcCode: str, attributeName: str, attributeContent: Any):
        """ Adds a named attribute to a function within the code, e.g. in a = myFunc(1,2,3)"""

        content = ast.parse(attributeContent, mode='eval').body

        codeAST = ast.parse(funcCode)

        class ReplaceOrAddNamedKeyword(ast.NodeTransformer):
            def visit_Expr(self, node):
                if isinstance(node.value, ast.Call):
                    node.value = self.modifyName(node.value)

                return self.generic_visit(node)

            def visit_Assign(self, node):
                if isinstance(node.value, ast.Call):
                    node.value = self.modifyName(node.value)

                return self.generic_visit(node)

            @staticmethod
            def modifyName(node):
                updated = False
                for kw in node.keywords:
                    if kw.arg == attributeName:
                        # Replace value of attribute of present
                        kw.value = content
                        updated = True
                        break

                if not updated:
                    # Add attribute
                    node.keywords.append(ast.keyword(arg=attributeName, value=content))

                return node

        codeAST = ReplaceOrAddNamedKeyword().visit(codeAST)

        return ast.unparse(codeAST)

    @staticmethod
    def toggleWarnings(warnings: bool):
        global _printCodeExtractorWarnings

        _printCodeExtractorWarnings = warnings


class ImportExtractor:
    class Result:
        def __init__(self, importEntries: List[ImportExtractor.ImportEntry],
                     targetAst: Module):
            self.importEntries = importEntries
            self.targetAst = targetAst

        def hasInternalImports(self) -> bool:
            for imp in self.importEntries:
                if imp.internal:
                    return True

            return False

        def toImportAst(self, skipInternal: bool = True) -> Module:
            impList = [i.importAst for i in self.importEntries if (skipInternal and not i.internal or not skipInternal)]
            return ast.fix_missing_locations(ast.Module(body=impList, type_ignores=[]))

    class ImportEntry:
        def __init__(self, importAst: Union[ast.Import, ast.ImportFrom], internal: bool):
            self.importAst = importAst
            self.internal = internal

            def getFilePath(module):
                """ Given a module name, return its file path.
                This assumes that the module is either part of the standard library or installed in the environment. """

                try:
                    # noinspection PyUnresolvedReferences
                    spec = importlib.util.find_spec(module)
                    if spec and spec.origin:
                        return spec.origin
                except ModuleNotFoundError:
                    return None
                return None

            if isinstance(importAst, ast.Import):
                # Handle regular imports (import <module>)
                for alias in importAst.names:
                    moduleName = alias.name
                    filePath = getFilePath(moduleName)

                    self.filePath = filePath
                    self.moduleName = moduleName
            elif isinstance(importAst, ast.ImportFrom):
                # Handle from imports (from <module> import <class>)
                module_name = importAst.module
                filePath = getFilePath(module_name)

                for alias in importAst.names:
                    className = alias.name

                    self.filePath = filePath
                    self.moduleName = className

    @staticmethod
    def extractUsedImports(fileAst: Optional[Module], targetAst: Module, removeImportsFromTarget: bool) -> Result:
        # Collect all top-level imports from the class file

        imports = set()

        if fileAst is not None:
            for node in ast.walk(fileAst):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.add(node)

        # Collect all imports from the function (which might be udf not included in file)

        for node in ast.walk(targetAst):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.add(node)

        # Collect names and attributes used in the target function

        usedNames = set()

        class NameCollector(ast.NodeVisitor):
            def visit_Name(self, n):
                usedNames.add(n.id)

                self.generic_visit(n)

            def visit_Attribute(self, n):
                # Add the base name of the attribute (e.g., 'json' in 'json.loads')
                if isinstance(n.value, ast.Name):
                    usedNames.add(n.value.id)

                self.generic_visit(n)

        NameCollector().visit(targetAst)

        # Match used names with imports

        importEntries: List[ImportExtractor.ImportEntry] = []

        def addImportEntry(im: Union[ast.Import, ast.ImportFrom]):
            if isinstance(im, ast.Import):  # Extract all module names from regular imports
                for al in imp.names:
                    importEntries.append(ImportExtractor.ImportEntry(im, ImportExtractor._isInternal(al.name)))
            elif isinstance(im, ast.ImportFrom):  # Extract the module and specific imports for from imports
                importEntries.append(ImportExtractor.ImportEntry(im, ImportExtractor._isInternal(imp.module)))

        for imp in imports:
            if isinstance(imp, ast.Import):
                for alias in imp.names:  # Multiple import in one line
                    # Only add portion of import which is actually used
                    if alias.asname and alias.asname in usedNames or alias.name in usedNames:
                        addImportEntry(ast.Import(names=[alias],))

            elif isinstance(imp, ast.ImportFrom):
                for alias in imp.names:  # Multiple imports such as from typing import Dict, Tuple, ...
                    # Only add portion of import which is actually used
                    if alias.asname and alias.asname in usedNames or alias.name in usedNames:
                        addImportEntry(ast.ImportFrom(
                            module=imp.module,
                            names=[alias],
                            level=imp.level
                        ))

        if removeImportsFromTarget:
            body = list()

            for node in targetAst.body:
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    body.append(node)

            targetAst = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))

        return ImportExtractor.Result(importEntries, targetAst)

    @staticmethod
    def resolveAliasImports(fileAst: Optional[Module], targetAst: Module) -> tuple[Module, Module]:
        """ Removes alias from both the imports and the code. """

        aliasMap = ImportExtractor.findImportAlias(fileAst if fileAst is not None else targetAst)

        fileAst = ImportExtractor.replaceAlias(fileAst, aliasMap) if fileAst is not None else None
        targetAst = ImportExtractor.replaceAlias(targetAst, aliasMap)

        return fileAst, targetAst

    @staticmethod
    def findImportAlias(targetAst: Module) -> Dict[str, str]:
        """ Detects alias from the import section. """

        class AliasDetector(ast.NodeTransformer):
            def __init__(self):
                self.aliasMap = {}

            def visit_Import(self, node):
                for alias in node.names:
                    if alias.asname:
                        self.aliasMap[alias.asname] = alias.name
                return node

            def visit_ImportFrom(self, node):
                for alias in node.names:
                    if alias.asname:
                        self.aliasMap[alias.asname] = alias.name
                return node

        at = AliasDetector()
        at.visit(targetAst)

        return at.aliasMap

    @staticmethod
    def replaceAlias(targetAst: Module, aliasMap: Dict[str, str]) -> Module:
        """ Removes alias from the import and code section. """

        class AliasRemover(ast.NodeTransformer):
            def visit_Import(self, node):
                for alias in node.names:
                    if alias.asname and alias.asname in aliasMap:
                        alias.asname = None  # Remove alias
                return node

            def visit_ImportFrom(self, node):
                for alias in node.names:
                    if alias.asname and alias.asname in aliasMap:
                        alias.asname = None  # Remove alias
                return node

            def visit_Name(self, node):
                if node.id in aliasMap:
                    node.id = aliasMap[node.id]
                return node

            def visit_Attribute(self, node):
                self.generic_visit(node)

                if isinstance(node.value, ast.Name) and node.value.id in aliasMap:
                    node.value.id = aliasMap[node.value.id]

                return node

        return AliasRemover().visit(targetAst)

    @staticmethod
    def _isInternal(impName: str):
        for subdir in _internalProjectDirs:
            if impName.startswith(subdir):
                return True

        return False


class ClassExtractor:
    """ Extracts a given class with its used imports.
    We assume, that we can extract any (internal) class that does not have other references to our internal SV system."""

    class Result:
        def __init__(self, moduleName: str, imports: str, classCode: str, internalImports: bool):
            self.moduleName = moduleName
            self.imports = imports
            self.classCode = classCode
            self.internalImports = internalImports

    def __init__(self, className: str, descriptor: Union[str, type]):
        self.className = className

        if isinstance(descriptor, str):
            self.classPath = descriptor
        elif isinstance(descriptor, type):
            self.classPath = inspect.getfile(descriptor)
        else:
            self.classPath = None

    def extract(self, allowInternalImports: bool) -> Optional[ClassExtractor.Result]:
        with open(self.classPath, 'r') as f:
            sourceCode = f.read()

        # Parse the entire file into an AST

        sourceAst = ast.parse(sourceCode)

        classAst = self.extractClassAst(sourceAst, self.className, False)

        if classAst is None:
            printError(f"Class {self.className} not found to extract in path {self.classPath}!")

            return None

        sourceAst, classAst = ImportExtractor.resolveAliasImports(sourceAst, classAst)
        importRes = ImportExtractor.extractUsedImports(sourceAst, classAst, True)

        if importRes.hasInternalImports() and not allowInternalImports:
            printError(f"Class {self.className} has internal imports to the SV system!")

            return None

        bodyCode = ast.unparse(importRes.targetAst)
        importCode = ast.unparse(importRes.toImportAst())

        return ClassExtractor.Result(self.className, importCode, bodyCode, importRes.hasInternalImports())

    @staticmethod
    def extractClassAst(fileAst: Module, targetClassName: str, bodyOnly: bool) -> Optional[Module]:
        for node in ast.walk(fileAst):
            if isinstance(node, ast.ClassDef) and node.name == targetClassName:
                returnAst = [node] if not bodyOnly else node.body
                return ast.fix_missing_locations(ast.Module(body=returnAst, type_ignores=[]))

        return None


class ModuleExtractor:
    """ Extracts a given module with its used imports.
    We assume, that we can extract any (internal) module that does not have other references to our internal SV system."""

    class Result:
        def __init__(self, imports: str, moduleCode: str, internalImports: bool):
            self.imports = imports
            self.moduleCode = moduleCode
            self.internalImports = internalImports

    def __init__(self, descriptor: Union[str, types.ModuleType]):
        if isinstance(descriptor, str):
            self.modulePath = descriptor
        elif isinstance(descriptor, types.ModuleType):
            self.modulePath = descriptor.__file__
        else:
            self.modulePath = None

    def extract(self, allowInternalImports: bool) -> Optional[ModuleExtractor.Result]:
        if self.modulePath is None:
            return None

        with open(self.modulePath, 'r') as f:
            sourceCode = f.read()

        # Parse the entire file into an AST

        sourceAst = ast.parse(sourceCode)

        _, sourceAst = ImportExtractor.resolveAliasImports(None, sourceAst)
        importRes = ImportExtractor.extractUsedImports(None, sourceAst, True)

        if importRes.hasInternalImports() and not allowInternalImports:
            printError(f"Module {self.modulePath} has internal imports to the SV system!")

            return None

        bodyCode = ast.unparse(importRes.targetAst)
        importCode = ast.unparse(importRes.toImportAst())

        return ModuleExtractor.Result(importCode, bodyCode, importRes.hasInternalImports())


_printCodeExtractorWarnings = True


def printError(err: str):
    if _printCodeExtractorWarnings:
        printWarning(err)


def _getInternalDirs():
    """ Get all subdirectories inside the root folder of the system. """

    subDirs = []

    for root, dirs, _ in os.walk(StreamVizzard.getRootSrcPath()):
        cleanedDirs = [d for d in dirs if d != "__pycache__"]
        subDirs.extend(cleanedDirs)
        subDirs.append(os.path.basename(root))

        break

    return subDirs


_internalProjectDirs: List[str] = _getInternalDirs()
