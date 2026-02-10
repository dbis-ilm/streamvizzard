import Threshold from "@/scripts/pipeline/operators/modules/imageproc/operators/process/Threshold";
import EqHistogram from "@/scripts/pipeline/operators/modules/imageproc/operators/process/EqHistogram";
import CalcHistogram from "@/scripts/pipeline/operators/modules/imageproc/operators/process/CalcHistogram";
import GaussianBlur from "@/scripts/pipeline/operators/modules/imageproc/operators/process/GaussianBlur";
import Canny from "@/scripts/pipeline/operators/modules/imageproc/operators/process/Canny";
import FindContours from "@/scripts/pipeline/operators/modules/imageproc/operators/process/FindContours";

let getComponents = (pathIdentifier) => {
    return [new Threshold(pathIdentifier), new EqHistogram(pathIdentifier),
        new CalcHistogram(pathIdentifier), new GaussianBlur(pathIdentifier),
        new Canny(pathIdentifier), new FindContours(pathIdentifier)];
}

export default {Threshold, EqHistogram, GaussianBlur, Canny, FindContours, CalcHistogram, getComponents}
