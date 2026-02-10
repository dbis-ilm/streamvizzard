import Highpass from "@/scripts/pipeline/operators/modules/signalProc/operators/Highpass";
import Lowpass from "@/scripts/pipeline/operators/modules/signalProc/operators/Lowpass";
import Bandpass from "@/scripts/pipeline/operators/modules/signalProc/operators/Bandpass";
import Resample from "@/scripts/pipeline/operators/modules/signalProc/operators/Resample";
import FlattenSignals from "@/scripts/pipeline/operators/modules/signalProc/operators/FlattenSignals";

let getComponents = (pathIdentifier) => {
    return [new Highpass(pathIdentifier), new Lowpass(pathIdentifier),
    new Bandpass(pathIdentifier),
    new Resample(pathIdentifier), new FlattenSignals(pathIdentifier)]
}

export default {Highpass, Lowpass, Bandpass, Resample, FlattenSignals, getComponents}
