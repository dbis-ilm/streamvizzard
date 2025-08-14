import VideoFile from "@/scripts/components/modules/imageproc/sources/VideoFile";
import WebCam from "@/scripts/components/modules/imageproc/sources/WebCam";
import {isDockerExecution} from "@/scripts/streamVizzard";

let getComponents = (pathIdentifier) => {
    let ops = [new VideoFile(pathIdentifier)];

    if(!isDockerExecution()) ops.push(new WebCam(pathIdentifier));

    return ops;
}

export default {VideoFile, WebCam, getComponents}
