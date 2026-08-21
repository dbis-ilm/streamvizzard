import Microphone from "@/scripts/pipeline/operators/modules/signalProc/sources/Microphone";
import AudioFile from "@/scripts/pipeline/operators/modules/signalProc/sources/AudioFile";
import WhiteNoise from "@/scripts/pipeline/operators/modules/signalProc/sources/WhiteNoise";
import {SvInstance} from "@/scripts/StreamVizzard";


let getComponents = (pathIdentifier) => {
    let ops = [new AudioFile(pathIdentifier), new WhiteNoise(pathIdentifier)];

    if (!SvInstance.isDockerExecution()) ops.push(new Microphone(pathIdentifier));

    return ops;
}

export default {Microphone, AudioFile, WhiteNoise, getComponents}
