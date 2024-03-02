from typing import List, Optional

# TODO: Currently unused, only required for code generation


class Stream:
    def __init__(self, streamID: int):
        self.id = streamID

        # Ordered list of all operators that take part in this stream

        from spe.pipeline.operators.operator import Operator
        self.operators: List[Operator] = list()

        self.initialOperator: Optional[Operator] = None  # Never a source

    def registerOperator(self, operator):
        self.operators.append(operator)

        # operator.stream = self

        if self.initialOperator is None and not operator.isSource():
            self.initialOperator = operator

    def removeOperator(self, operator):
        self.operators.remove(operator)

        if len(self.operators) == 0:
            self.initialOperator = None

            return

        # Find a new initial operator in case the current was removed

        for op in self.operators:
            if not op.isSource():
                self.initialOperator = op

                break
