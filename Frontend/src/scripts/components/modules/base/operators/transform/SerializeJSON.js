import {Component} from "@/scripts/components/Component";
import {strSocket} from "@/scripts/components/modules/base";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";

export default class _SerializeJSON extends Component {
    constructor(pathIdentifier){
        super("SerializeJSON", "Serialize JSON", pathIdentifier);
    }

    builder(node) {
        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: "JSON", socket: anySocket}],
            [{name: strSocket.name, socket: strSocket}],
            []);
    }
}
