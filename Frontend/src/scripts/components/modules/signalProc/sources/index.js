import Microphone from "@/scripts/components/modules/signalProc/sources/Microphone";
import AudioFile from "@/scripts/components/modules/signalProc/sources/AudioFile";
import {isDockerExecution} from "@/scripts/streamVizzard";


let getComponents = (pathIdentifier) => {
    let ops = [new AudioFile(pathIdentifier)];

    if (!isDockerExecution()) ops.push(new Microphone(pathIdentifier));

    return ops;
}

export default {Microphone, AudioFile, getComponents}
