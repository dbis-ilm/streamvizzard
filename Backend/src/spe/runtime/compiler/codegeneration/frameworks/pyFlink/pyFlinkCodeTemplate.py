from __future__ import annotations

from enum import Enum
from string import Template
from typing import Dict, Optional, List, Union

from spe.runtime.compiler.codegeneration.codeTemplate import CodeTemplate
from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkUtils import PyFlinkJARs, PyFlinkStruct, PyFlinkTags


class PyFlinkCodeTemplate(CodeTemplate):
    """ Must contain placeholders:
    Section: ASSIGNMENTS
    $inDS: The dataStream which this operator should be added to | e.g. usage: $inDS.add_sink(...)
    Section: FUNCTION_CONTENT
    $input: For accessing the input data, if operator has more than one input, array access must be used $input[0]
    ---
    For single output operators, the functions must manually return only one value and not a tuple!
    For single input operators, $input[0] access is automatically replaced with $input
    Can either declare FUNCTION_CONTENT OR FUNCTION_DECLARATION.
    FUNCTION_CONTENT will be extracted into a generated function, such as map
    ASSIGNMENTS supports a list of separate assignment calls added in order to op
    """

    def __init__(self, entries: Dict[Section, Union[str, List[str]]], jarDependencies: Optional[List[PyFlinkJARs]] = None,
                 structDependencies: Optional[List[PyFlinkStruct]] = None, tags: Optional[List[PyFlinkTags]] = None):
        args = dict()

        for k in entries:
            args[k.value] = entries[k]

        super().__init__(**args)

        self.jarDependencies = jarDependencies if jarDependencies is not None else []
        self.structDependencies = structDependencies if structDependencies is not None else []
        self.tags = tags if tags is not None else []

    def get(self, section: Section) -> Optional[Union[Template, List[Template]]]:
        return self.getTemplate(section.value)

    def hasTag(self, tag: PyFlinkTags):
        return tag in self.tags

    class Section(Enum):
        IMPORTS = "imports"
        FUNCTION_CONTENT = "functionContent"
        FUNCTION_DECLARATION = "functionDeclaration"
        ASSIGNMENTS = "assignments"
