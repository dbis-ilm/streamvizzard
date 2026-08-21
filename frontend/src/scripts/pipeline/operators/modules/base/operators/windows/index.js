import TumblingWindowCount from "@/scripts/pipeline/operators/modules/base/operators/windows/TumblingWindowCount";
import TumblingWindowTime from "@/scripts/pipeline/operators/modules/base/operators/windows/TumblingWindowTime";
import SlidingWindowCount from "@/scripts/pipeline/operators/modules/base/operators/windows/SlidingWindowCount";
import SlidingWindowTime from "@/scripts/pipeline/operators/modules/base/operators/windows/SlidingWindowTime";
import WindowCollect from "@/scripts/pipeline/operators/modules/base/operators/windows/WindowCollect";

let getComponents = (pathIdentifier) => {
    return [new TumblingWindowCount(pathIdentifier), new TumblingWindowTime(pathIdentifier),
        new SlidingWindowCount(pathIdentifier), new SlidingWindowTime(pathIdentifier),
        new WindowCollect(pathIdentifier)];
}

export default {TumblingWindowCount, TumblingWindowTime, SlidingWindowCount, WindowCollect, getComponents}
