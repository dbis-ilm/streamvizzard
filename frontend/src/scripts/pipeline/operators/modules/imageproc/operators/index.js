import Math from "@/scripts/pipeline/operators/modules/imageproc/operators/math";
import Transform from "@/scripts/pipeline/operators/modules/imageproc/operators/transform";
import Process from "@/scripts/pipeline/operators/modules/imageproc/operators/process";

let getComponents = (pathIdentifier) => {
    return Process.getComponents(pathIdentifier.concat("Process"))
        .concat(Math.getComponents(pathIdentifier.concat("Math")))
        .concat(Transform.getComponents(pathIdentifier.concat("Transform")))
}

export default {Math, Transform, Process, getComponents}
