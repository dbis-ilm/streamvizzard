import ToInt from "@/scripts/pipeline/operators/modules/base/operators/transform/ToInt";
import ToBool from "@/scripts/pipeline/operators/modules/base/operators/transform/ToBool";
import ToFloat from "@/scripts/pipeline/operators/modules/base/operators/transform/ToFloat";
import ToString from "@/scripts/pipeline/operators/modules/base/operators/transform/ToString";
import StringSplit from "@/scripts/pipeline/operators/modules/base/operators/transform/StringSplit";
import Combine from "@/scripts/pipeline/operators/modules/base/operators/transform/Combine";
import ParseJSON from "@/scripts/pipeline/operators/modules/base/operators/transform/ParseJSON";
import SerializeJSON from "@/scripts/pipeline/operators/modules/base/operators/transform/SerializeJSON";

let getComponents = (pathIdentifier) => {
    return [new ToInt(pathIdentifier), new ToFloat(pathIdentifier), new ToString(pathIdentifier),
        new ToBool(pathIdentifier), new StringSplit(pathIdentifier), new Combine(pathIdentifier), new ParseJSON(pathIdentifier),
    new SerializeJSON(pathIdentifier)];
}

export default {ToInt, ToBool, ToFloat, ToString, StringSplit, Combine, ParseJSON, getComponents}
