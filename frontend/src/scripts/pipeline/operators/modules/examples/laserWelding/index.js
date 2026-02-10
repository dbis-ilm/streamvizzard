import LSTMPrediction from "@/scripts/pipeline/operators/modules/examples/laserWelding/LSTMPrediction";
import CNNPrediction from "@/scripts/pipeline/operators/modules/examples/laserWelding/CNNPrediction";

let getComponents = (pathIdentifier) => {
    return [new LSTMPrediction(pathIdentifier), new CNNPrediction(pathIdentifier)]
}

export default {LSTMPrediction, CNNPrediction, getComponents}
