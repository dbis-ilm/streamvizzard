import {Component} from "@/scripts/components/Component";
import {NUMBER_DT, numSocket, primitiveSocket} from "@/scripts/components/modules/base";
import {Display} from "@/scripts/components/monitor/Display";

export default class _ToInt extends Component {
    constructor(pathIdentifier){
        super("ToInt", "To Int", pathIdentifier);
    }

    builder(node) {
        return this.onBuilderInitialized(node,
            new Display(node, NUMBER_DT.name),
            [{name: "Any", socket: primitiveSocket}],
            [{name: "Number", socket: numSocket}],
            []);
    }
}
