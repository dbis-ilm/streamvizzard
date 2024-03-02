import TumblingWindowCount from "@/scripts/components/modules/base/operators/windows/TumblingWindowCount";
import TumblingWindowTime from "@/scripts/components/modules/base/operators/windows/TumblingWindowTime";
import WindowCollect from "@/scripts/components/modules/base/operators/windows/WindowCollect";

let getComponents = (pathIdentifier) => {
    return [new TumblingWindowCount(pathIdentifier), new TumblingWindowTime(pathIdentifier), new WindowCollect(pathIdentifier)];
}

export default {TumblingWindowCount, TumblingWindowTime, WindowCollect, getComponents}
