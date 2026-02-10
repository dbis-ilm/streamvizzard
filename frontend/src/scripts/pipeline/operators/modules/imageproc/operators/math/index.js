import ImgAdd from "@/scripts/pipeline/operators/modules/imageproc/operators/math/ImgAdd";
import ImgMultiply from "@/scripts/pipeline/operators/modules/imageproc/operators/math/ImgMultiply";
import ImgBlend from "@/scripts/pipeline/operators/modules/imageproc/operators/math/ImgBlend";

let getComponents = (pathIdentifier) => {
    return [new ImgAdd(pathIdentifier), new ImgMultiply(pathIdentifier),
    new ImgBlend(pathIdentifier)];
}

export default {ImgAdd, ImgMultiply, ImgBlend, getComponents}
