import Microphone from "@/scripts/pipeline/operators/modules/signalProc/sources/Microphone";
import AudioFile from "@/scripts/pipeline/operators/modules/signalProc/sources/AudioFile";
import {SvInstance} from "@/scripts/StreamVizzard";


let getComponents = (pathIdentifier) => {
    let ops = [new AudioFile(pathIdentifier)];

    if (!SvInstance.isDockerExecution()) ops.push(new Microphone(pathIdentifier));

    return ops;
}

export default {Microphone, AudioFile, getComponents}
