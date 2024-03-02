import ToInt from "@/scripts/components/modules/base/operators/transform/ToInt";
import ToFloat from "@/scripts/components/modules/base/operators/transform/ToFloat";
import ToString from "@/scripts/components/modules/base/operators/transform/ToString";
import StringSplit from "@/scripts/components/modules/base/operators/transform/StringSplit";
import Combine from "@/scripts/components/modules/base/operators/transform/Combine";
import ParseJSON from "@/scripts/components/modules/base/operators/transform/ParseJSON";
import FlattenList from "@/scripts/components/modules/base/operators/transform/FlattenList";

let getComponents = (pathIdentifier) => {
    return [new ToInt(pathIdentifier), new ToFloat(pathIdentifier), new ToString(pathIdentifier),
    new StringSplit(pathIdentifier), new Combine(pathIdentifier), new ParseJSON(pathIdentifier),
    new FlattenList(pathIdentifier)];
}

export default {ToInt, ToFloat, ToString, StringSplit, Combine, ParseJSON, FlattenList, getComponents}
