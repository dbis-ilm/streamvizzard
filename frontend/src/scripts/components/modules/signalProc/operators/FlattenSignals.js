import {Component} from "@/scripts/components/Component";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";
import {signalSocket} from "@/scripts/components/modules/signalProc";

export default class _FlattenSignals extends Component {
    constructor(pathIdentifier){
        super("FlattenSignals", "Flatten Signals", pathIdentifier);
    }

    builder(node) {
        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: "Signals", socket: anySocket}],
            [{name: signalSocket.name, socket: signalSocket}],
            []);
    }
}
