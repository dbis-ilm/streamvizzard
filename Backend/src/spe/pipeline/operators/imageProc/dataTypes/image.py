class Image:
    def __init__(self, mat):
        self.mat = mat

    def getWidth(self):
        return self.mat.shape[1]

    def getHeight(self):
        return self.mat.shape[0]

    def isGrey(self):
        return not (len(self.mat.shape) != 2 and self.mat.shape[2] != 1)

    def clone(self):
        return Image(self.mat.copy())
