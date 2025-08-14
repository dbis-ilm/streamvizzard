import textwrap
from string import Template
from typing import Dict, Optional, Union, List


class CodeTemplate:
    def __init__(self, **kwargs):
        self.entries: Dict[str, Union[Template, List[Template]]] = dict()

        for key in kwargs:
            v = kwargs[key]

            if isinstance(v, str):
                self.entries[key] = Template(textwrap.dedent(v))
            elif isinstance(v, list):
                self.entries[key] = [Template(textwrap.dedent(vi)) for vi in v]

    def getTemplate(self, name: str) -> Optional[Union[Template, List[Template]]]:
        return self.entries.get(name)
