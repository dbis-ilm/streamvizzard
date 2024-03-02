import {Component} from "@/scripts/components/Component";
import {NUMBER_DT, strSocket} from "@/scripts/components/modules/base";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";

export default class _ToInt extends Component {
    constructor(pathIdentifier){
        super("ToString", "To String", pathIdentifier);
    }

    builder(node) {
        return this.onBuilderInitialized(node,
            new Display(node, NUMBER_DT.name),
            [{name: "Any", socket: anySocket}],
            [{name: "String", socket: strSocket}],
            []);
    }
}
