import {Component} from "@/scripts/components/Component";
import {strSocket} from "@/scripts/components/modules/base";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";

export default class _ParseJSON extends Component {
    constructor(pathIdentifier){
        super("ParseJSON", "Parse JSON", pathIdentifier);
    }

    builder(node) {
        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: strSocket.name, socket: strSocket}],
            [{name: "JSON", socket: anySocket}],
            []);
    }
}
