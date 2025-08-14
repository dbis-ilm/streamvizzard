import {Component} from "@/scripts/components/Component";
import {NUMBER_DT, primitiveSocket} from "@/scripts/components/modules/base";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";

export default class _ToBool extends Component {
    constructor(pathIdentifier){
        super("ToBool", "To Bool", pathIdentifier);
    }

    builder(node) {
        return this.onBuilderInitialized(node,
            new Display(node, NUMBER_DT.name),
            [{name: "Any", socket: primitiveSocket}],
            [{name: "Bool", socket: anySocket}],
            []);
    }
}
