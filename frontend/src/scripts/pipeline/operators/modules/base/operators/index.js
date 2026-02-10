import Transform from "@/scripts/pipeline/operators/modules/base/operators/transform"
import Windows from "@/scripts/pipeline/operators/modules/base/operators/windows"

import UDF from "@/scripts/pipeline/operators/modules/base/operators/UDF"
import Filter from "@/scripts/pipeline/operators/modules/base/operators/Filter"
import UDO from "@/scripts/pipeline/operators/modules/base/operators/UDO"

let getComponents = (pathIdentifier) => {
    return Transform.getComponents(pathIdentifier.concat("Transform"))
        .concat(Windows.getComponents(pathIdentifier.concat("Windows")))
        .concat([new UDO(pathIdentifier), new UDF(pathIdentifier), new Filter(pathIdentifier)]);
}

export default {Transform, Windows, UDF, Filter, UDO, getComponents}
