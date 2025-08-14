import Transform from "@/scripts/components/modules/base/operators/transform"
import Windows from "@/scripts/components/modules/base/operators/windows"

import UDF from "@/scripts/components/modules/base/operators/UDF"
import Filter from "@/scripts/components/modules/base/operators/Filter"
import UDO from "@/scripts/components/modules/base/operators/UDO"

let getComponents = (pathIdentifier) => {
    return Transform.getComponents(pathIdentifier.concat("Transform"))
        .concat(Windows.getComponents(pathIdentifier.concat("Windows")))
        .concat([new UDO(pathIdentifier), new UDF(pathIdentifier), new Filter(pathIdentifier)]);
}

export default {Transform, Windows, UDF, Filter, UDO, getComponents}
