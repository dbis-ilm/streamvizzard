import Cast from "@/scripts/pipeline/operators/modules/base/operators/transform/Cast";
import StringSplit from "@/scripts/pipeline/operators/modules/base/operators/transform/StringSplit";
import Combine from "@/scripts/pipeline/operators/modules/base/operators/transform/Combine";
import ParseJSON from "@/scripts/pipeline/operators/modules/base/operators/transform/ParseJSON";
import SerializeJSON from "@/scripts/pipeline/operators/modules/base/operators/transform/SerializeJSON";

let getComponents = (pathIdentifier) => {
    return [new Cast(pathIdentifier), new StringSplit(pathIdentifier), new Combine(pathIdentifier),
        new ParseJSON(pathIdentifier), new SerializeJSON(pathIdentifier)];
}

export default {Cast, StringSplit, Combine, ParseJSON, getComponents}
