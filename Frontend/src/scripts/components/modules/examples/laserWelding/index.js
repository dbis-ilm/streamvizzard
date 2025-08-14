import LSTMPrediction from "@/scripts/components/modules/examples/laserWelding/LSTMPrediction";
import CNNPrediction from "@/scripts/components/modules/examples/laserWelding/CNNPrediction";

let getComponents = (pathIdentifier) => {
    return [new LSTMPrediction(pathIdentifier), new CNNPrediction(pathIdentifier)]
}

export default {LSTMPrediction, CNNPrediction, getComponents}
