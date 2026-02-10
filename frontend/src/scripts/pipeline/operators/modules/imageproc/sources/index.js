import VideoFile from "@/scripts/pipeline/operators/modules/imageproc/sources/VideoFile";
import WebCam from "@/scripts/pipeline/operators/modules/imageproc/sources/WebCam";
import {SvInstance} from "@/scripts/StreamVizzard";

let getComponents = (pathIdentifier) => {
    let ops = [new VideoFile(pathIdentifier)];

    if(!SvInstance.isDockerExecution()) ops.push(new WebCam(pathIdentifier));

    return ops;
}

export default {VideoFile, WebCam, getComponents}
