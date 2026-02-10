import Convert from "@/scripts/pipeline/operators/modules/imageproc/operators/transform/Convert";
import ImgMerge from "@/scripts/pipeline/operators/modules/imageproc/operators/transform/ImgMerge";
import ImgSplit from "@/scripts/pipeline/operators/modules/imageproc/operators/transform/ImgSplit";
import ImgResize from "@/scripts/pipeline/operators/modules/imageproc/operators/transform/ImgResize";
import ImgLoad from "@/scripts/pipeline/operators/modules/imageproc/operators/transform/ImgLoad";
import ExtractROI from "@/scripts/pipeline/operators/modules/imageproc/operators/transform/ExtractROI";

let getComponents = (pathIdentifier) => {
    return [new Convert(pathIdentifier), new ImgMerge(pathIdentifier),
        new ImgSplit(pathIdentifier), new ImgResize(pathIdentifier),
        new ExtractROI(pathIdentifier), new ImgLoad(pathIdentifier)];
}

export default {Convert, ImgSplit, ImgMerge, ImgResize, ExtractROI, ImgLoad, getComponents}
