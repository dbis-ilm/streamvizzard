import {Component} from "@/scripts/components/Component";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";
import {SelectControl} from "@/scripts/components/modules/base/controls/SelectCtrl";


export default class _MissingValues extends Component {
    constructor(pathIdentifier){
        super("MissingValues", "Missing Values", pathIdentifier);
    }

    builder(node) {
     node.mode = new SelectControl(node, 'mode',
            false, [{title: "Linear", key: "linear"},
                {title: "Polynomial", key: "polynomial"},
                {title: "Padding", key: "padding"},
                {title: "Drop", key: "drop"},], "linear", "Replacement");
        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: "Any", socket: anySocket}],
            [{name: "Cleaned", socket: anySocket}],
            [node.mode]);
    }
}
