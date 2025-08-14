class CompileOpMetaData:
    def __init__(self, inheritTarget: bool = False):
        self.inheritTarget = inheritTarget  # If this operator inherits the compile target from its parent(s)
