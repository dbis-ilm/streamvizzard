import json
from typing import Optional

import numpy as np
import pandas as pd

from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


class MissingValues(Operator):
    def __init__(self, opID: int):
        super(MissingValues, self).__init__(opID, 1, 1)

        self.mode = None

    def setData(self, data: json):
        self.mode = data["mode"]  # [linear, polynomial, padding, drop]

    def getData(self) -> dict:
        return {"mode": self.mode}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        data = tupleIn.data[0]

        # For pandas version stability we need to explicitly set nan for missing values
        dataSeries = pd.Series([np.nan if v is None else v for v in data])

        if self.mode == "linear":
            df = dataSeries.interpolate(limit_direction='both')
        elif self.mode == "polynomial":
            # Need at least 3+1 non-missing values in data ...
            df = dataSeries.interpolate(method='polynomial', order=3, limit_direction='both')
        elif self.mode == "pad":
            df = dataSeries.interpolate(method='pad', limit=len(data), limit_direction='both')
        else:
            df = dataSeries
            df.dropna(inplace=True)

        data_frame = pd.DataFrame(df, columns=['data'])
        data_cleaned = list(data_frame.itertuples(index=True, name=None))

        data_cleaned_list = [t[1] for t in data_cleaned]

        return self.createTuple((data_cleaned_list,))
