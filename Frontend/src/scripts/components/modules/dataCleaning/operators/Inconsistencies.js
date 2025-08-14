import {Component} from "@/scripts/components/Component";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {SelectControl} from "@/scripts/components/modules/base/controls/SelectCtrl";



export default class _Inconsistencies extends Component {
    constructor(pathIdentifier){
        super("Inconsistencies", "Inconsistencies", pathIdentifier);
    }

 builder(node) {
        node.threshold = new NumControl(node, 'threshold', false, -100 , "Threshold", "" );
        node.maxValue = new NumControl(node, 'maxValue', false, 1000, "Max. Value", "");
        node.mode = new SelectControl(node, 'mode',
            false, [{title: "Mean", key: "mean"}, {title: "Mode", key: "mode"},
                {title: "Median", key: "median"}, {title: "Remove", key: "remove"}], "mean", "Replacement");

       return this.onBuilderInitialized(node,
            new Display(node),
            [{name: "Any", socket: anySocket}],
            [{name: "Cleaned", socket: anySocket}, {name: "Invalid", socket: anySocket}],
            [node.threshold, node.maxValue,node.mode]);
    }
}



