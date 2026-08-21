import Filter from "@/scripts/pipeline/operators/modules/signalProc/operators/filter";
import Resample from "@/scripts/pipeline/operators/modules/signalProc/operators/Resample";
import Gain from "@/scripts/pipeline/operators/modules/signalProc/operators/Gain";
import FlattenSignals from "@/scripts/pipeline/operators/modules/signalProc/operators/FlattenSignals";
import ExtractChannels from "@/scripts/pipeline/operators/modules/signalProc/operators/ExtractChannels";
import CombineChannels from "@/scripts/pipeline/operators/modules/signalProc/operators/CombineChannels";

let getComponents = (pathIdentifier) => {
    return Filter.getComponents(pathIdentifier.concat("Filter")).concat(
        [new Resample(pathIdentifier), new FlattenSignals(pathIdentifier), new Gain(pathIdentifier),
        new ExtractChannels(pathIdentifier), new CombineChannels(pathIdentifier)])
}

export default {Resample, FlattenSignals, Gain, ExtractChannels, CombineChannels, getComponents}
