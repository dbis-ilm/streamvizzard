import TumblingWindowCount from "@/scripts/pipeline/operators/modules/base/operators/windows/TumblingWindowCount";
import TumblingWindowTime from "@/scripts/pipeline/operators/modules/base/operators/windows/TumblingWindowTime";
import WindowCollect from "@/scripts/pipeline/operators/modules/base/operators/windows/WindowCollect";

let getComponents = (pathIdentifier) => {
    return [new TumblingWindowCount(pathIdentifier), new TumblingWindowTime(pathIdentifier), new WindowCollect(pathIdentifier)];
}

export default {TumblingWindowCount, TumblingWindowTime, WindowCollect, getComponents}
