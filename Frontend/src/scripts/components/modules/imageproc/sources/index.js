import VideoFile from "@/scripts/components/modules/imageproc/sources/VideoFile";
import WebCam from "@/scripts/components/modules/imageproc/sources/WebCam";

let getComponents = (pathIdentifier) => {
    return [new VideoFile(pathIdentifier), new WebCam(pathIdentifier)];
}

export default {VideoFile, WebCam, getComponents}
