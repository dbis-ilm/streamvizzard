import AnomalyDetection from "@/scripts/components/modules/dataCleaning/operators/AnomalyDetection";
import MissingValues from "@/scripts/components/modules/dataCleaning/operators/MissingValues";
import Inconsistency from "@/scripts/components/modules/dataCleaning/operators/Inconsistencies";

let getComponents = (pathIdentifier) => {
    return [new MissingValues(pathIdentifier), new Inconsistency(pathIdentifier), new AnomalyDetection(pathIdentifier)];
}

export default {MissingValues, Inconsistency, AnomalyDetection, getComponents}


