import Threshold from "@/scripts/components/modules/imageproc/operators/process/Threshold";
import EqHistogram from "@/scripts/components/modules/imageproc/operators/process/EqHistogram";
import GaussianBlur from "@/scripts/components/modules/imageproc/operators/process/GaussianBlur";
import Canny from "@/scripts/components/modules/imageproc/operators/process/Canny";
import FindContours from "@/scripts/components/modules/imageproc/operators/process/FindContours";

let getComponents = (pathIdentifier) => {
    return [new Threshold(pathIdentifier), new EqHistogram(pathIdentifier),
        new GaussianBlur(pathIdentifier), new Canny(pathIdentifier),
        new FindContours(pathIdentifier)];
}

export default {Threshold, EqHistogram, GaussianBlur, Canny, FindContours, getComponents}
