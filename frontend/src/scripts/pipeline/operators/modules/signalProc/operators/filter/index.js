import Highpass from "@/scripts/pipeline/operators/modules/signalProc/operators/filter/Highpass";
import Lowpass from "@/scripts/pipeline/operators/modules/signalProc/operators/filter/Lowpass";
import Bandpass from "@/scripts/pipeline/operators/modules/signalProc/operators/filter/Bandpass";
import NotchFilter from "@/scripts/pipeline/operators/modules/signalProc/operators/filter/NotchFilter";

let getComponents = (pathIdentifier) => {
    return [new Highpass(pathIdentifier), new Lowpass(pathIdentifier),
    new Bandpass(pathIdentifier), new NotchFilter(pathIdentifier)]
}

export default {Highpass, Lowpass, Bandpass, NotchFilter, getComponents}
