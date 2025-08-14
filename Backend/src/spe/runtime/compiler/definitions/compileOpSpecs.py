from __future__ import annotations
from typing import List, Dict, Optional, TYPE_CHECKING, Callable

from spe.runtime.compiler.definitions.compileDefinitions import CompileLanguage, CompileComputeMode, CompileParallelism, \
    CompileFramework
from spe.runtime.compiler.opCompileConfig import OpCompileConfig
from spe.runtime.compiler.definitions.compileOpFunction import InferExecutionCodeCOF

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator
    from spe.runtime.compiler.definitions.compileOpFunction import CompileOpFunction
    from spe.runtime.compiler.definitions.compileFrameworkSpecs import CompileFrameworkSpecs


class CompileOpSpecs:
    def __init__(self, frameworks: List[CompileFramework],
                 languages: List[CompileLanguage],
                 computeModes: List[CompileComputeMode],
                 parallelisms: List[CompileParallelism],
                 supportedCheck: Optional[Callable[[], bool]] = None,
                 compileFunction: Optional[CompileOpFunction] = None):
        self.languages = languages
        self.computeModes = computeModes
        self.frameworks = frameworks
        self.parallelisms = parallelisms

        # Custom function that might take op params into account to check if this config is supported
        self.supportedCheck = supportedCheck

        # Function used to generate the operator code during compilation
        self.compileFunction = compileFunction

    @staticmethod
    def getDefaultInferable():
        return CompileOpSpecs(CompileFramework.all(),
                              [CompileLanguage.PYTHON],
                              [CompileComputeMode.CPU],
                              CompileParallelism.all(),
                              compileFunction=InferExecutionCodeCOF(InferExecutionCodeCOF.Type.MAP))

    @staticmethod
    def getSVDefault():
        return CompileOpSpecs([CompileFramework.STREAMVIZZARD],
                              [CompileLanguage.PYTHON],
                              [CompileComputeMode.CPU],
                              [CompileParallelism.SINGLE_NODE],
                              compileFunction=InferExecutionCodeCOF(InferExecutionCodeCOF.Type.MAP))


class CompileOpSpecsCatalog:
    """ Merged view of all operator compile specs with the respective framework specs of the system. """

    class Language:
        def __init__(self, language: CompileLanguage,
                     supportedComputeModes: List[CompileComputeMode],
                     supportedParallelism: List[CompileParallelism]):
            self.language = language
            self.supportedComputeModes = supportedComputeModes

            # ComputeMode determines supported Parallelism since ComputeMode and Parallelism have an M:N cardinality
            self.supportedParallelism: Dict[CompileComputeMode, List[CompileParallelism]] = dict()

            for sTM in supportedComputeModes:
                self.supportedParallelism[sTM] = supportedParallelism

        def mergeLanguage(self, otherLanguage: CompileOpSpecsCatalog.Language):
            # Merge compute modes
            origCM = set(self.supportedComputeModes)
            otherCM = set(otherLanguage.supportedComputeModes)

            self.supportedComputeModes = CompileComputeMode.orderList(list(origCM.union(otherCM)))

            # Union existing Parallelisms for CMs with new ones
            for p in self.supportedParallelism:
                otherPs = otherLanguage.supportedParallelism.get(p, None)

                if otherPs is None:
                    continue

                origPs = set(self.supportedParallelism[p])
                otherPs = set(otherPs)

                self.supportedParallelism[p] = CompileParallelism.orderList(list(origPs.union(otherPs)))

            # Introduce new Parallelism entries
            for newCM in otherLanguage.supportedComputeModes:
                otherPs = otherLanguage.supportedParallelism.get(newCM, None)

                if otherPs is None:
                    continue

                if newCM not in self.supportedParallelism:
                    self.supportedParallelism[newCM] = otherPs

        def supportsComputeMode(self, computeMode: CompileComputeMode) -> bool:
            for cm in self.supportedComputeModes:
                if cm == computeMode:
                    return True

            return False

        def supportsParallelism(self, computeMode: CompileComputeMode, parallelism: CompileParallelism) -> bool:
            for p in self.supportedParallelism.get(computeMode, []):
                if p == parallelism:
                    return True

            return False

        def verifySupported(self, framework: CompileFrameworkSpecs) -> bool:
            # Checks if this language entry is supported by the framework [must at least match one CM, Parallelism]
            # Adapts computeModes, parallelism that is not supported by the framework

            if self.language not in framework.supportedLanguages:
                return False

            self.supportedComputeModes = CompileComputeMode.orderList(
                list(set(self.supportedComputeModes).intersection(set(framework.supportedComputeModes))))

            if len(self.supportedComputeModes) == 0:
                return False

            pKeys = list(self.supportedParallelism.keys())

            for tm in pKeys:
                p = self.supportedParallelism[tm]

                self.supportedParallelism[tm] = CompileParallelism.orderList(
                    list(set(p).intersection(set(framework.supportedParallelism))))

                if len(self.supportedParallelism[tm]) == 0:
                    self.supportedParallelism.pop(tm)

            if len(self.supportedParallelism) == 0:
                return False

            return True

    class Framework:
        def __init__(self, framework: CompileFramework,
                     supportedLanguages: List[CompileOpSpecsCatalog.Language]):
            self.framework = framework
            self.supportedLanguages = supportedLanguages

        def getLanguage(self, language: CompileLanguage) -> Optional[CompileOpSpecsCatalog.Language]:
            for lan in self.supportedLanguages:
                if lan.language == language:
                    return lan

            return None

        def mergeFramework(self, otherFramework: CompileOpSpecsCatalog.Framework):
            for language in otherFramework.supportedLanguages:
                currentLanguage = self.getLanguage(language.language)

                # New language doesn't exist in prev framework
                if currentLanguage is None:
                    self.supportedLanguages.append(language)
                else:  # Language exists -> merge!
                    currentLanguage.mergeLanguage(language)

    def __init__(self, operator: Operator):
        self.operator = operator
        self.frameworks: List[CompileOpSpecsCatalog.Framework] = []

        from spe.runtime.compiler.definitions.compileFrameworkSpecs import getSupportedFramework

        cfgs = operator.getCompileSpecs()

        for cfg in cfgs:
            # Check if cfg has a custom support check

            if (cfg.supportedCheck is not None
                    and not cfg.supportedCheck()):
                continue

            for fw in cfg.frameworks:
                # Check if this framework is supported by the system
                framework = getSupportedFramework(fw)

                if framework is None:
                    continue

                # Check if the framework has a custom support check

                if (framework.supportedCheck is not None
                        and not framework.supportedCheck(operator)):
                    continue

                newLanguages: List[CompileOpSpecsCatalog.Language] = []

                # Add all languages for the framework with all computeModes and parallelisms listed in the cfg

                for lang in cfg.languages:
                    newLanguage = CompileOpSpecsCatalog.Language(lang, cfg.computeModes, cfg.parallelisms)

                    if not newLanguage.verifySupported(framework):
                        continue

                    newLanguages.append(newLanguage)

                # Add or update framework (if we have any supported languages)

                if len(newLanguages) == 0:
                    continue

                newEnv = CompileOpSpecsCatalog.Framework(fw, newLanguages)

                prevFramework = self.getFramework(newEnv.framework)

                if prevFramework is None:
                    self.frameworks.append(newEnv)
                else:
                    prevFramework.mergeFramework(newEnv)

    def createDefaultCompileConfig(self) -> OpCompileConfig:
        t = OpCompileConfig()

        fw = self.frameworks[0]
        lang = fw.supportedLanguages[0]
        t.framework = fw.framework
        t.language = lang.language
        t.computeMode = lang.supportedComputeModes[0]
        t.parallelism = lang.supportedParallelism[t.computeMode][0]
        t.parallelismCount = 1 if t.parallelism == CompileParallelism.SINGLE_NODE else 2

        return t

    def getFramework(self, env: CompileFramework) -> Optional[Framework]:
        for e in self.frameworks:
            if e.framework == env:
                return e

        return None

    def deriveEnvRules(self) -> List[Dict]:
        frameworks = []

        for framework in self.frameworks:
            languages = []

            for language in framework.supportedLanguages:
                computeModes = []

                for cm in language.supportedComputeModes:
                    computeMode = {"key": cm.value}

                    parallelisms = language.supportedParallelism.get(cm, None)

                    computeMode["parallelism"] = [p.value for p in parallelisms] if parallelisms is not None else []

                    computeModes.append(computeMode)

                languages.append({"key": language.language.value, "computeModes": computeModes})

            frameworks.append({"key": framework.framework.value, "languages": languages})

        return frameworks

    def verifyOpCompileConfig(self, cfg: OpCompileConfig) -> bool:
        # Verify that the config is valid and supported by the operator compile specs

        framework = self.getFramework(cfg.framework)

        if framework is None:
            return False

        target = framework.getLanguage(cfg.language)

        if target is None:
            return False

        if not target.supportsComputeMode(cfg.computeMode):
            return False

        if not target.supportsParallelism(cfg.computeMode, cfg.parallelism):
            return False

        return True

    def getCompileFunction(self, config: OpCompileConfig):
        compileCfgs = self.operator.getCompileSpecs()

        for cc in compileCfgs:
            if (config.framework is None or
                    config.framework not in cc.frameworks):
                continue

            if (config.language is None or
                    config.language not in cc.languages):
                continue

            if (config.computeMode is None or
                    config.computeMode not in cc.computeModes):
                continue

            if (config.parallelism is None or
                    config.parallelism not in cc.parallelisms):
                continue

            if cc.compileFunction is not None:
                return cc.compileFunction

        return None
