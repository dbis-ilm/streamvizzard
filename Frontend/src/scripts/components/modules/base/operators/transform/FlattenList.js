import {Component} from "@/scripts/components/Component";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";

export default class _FlattenList extends Component {
    constructor(pathIdentifier){
        super("FlattenList", "Flatten List", pathIdentifier);
    }

    builder(node) {
        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: "Any", socket: anySocket}],
            [{name: "Array", socket: anySocket}],
            []);
    }
}
