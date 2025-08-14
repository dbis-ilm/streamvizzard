import {Component} from "@/scripts/components/Component";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";

export default class _WindowCollect extends Component {
    constructor(pathIdentifier){
        super("WindowCollect", "Window Collect", pathIdentifier);
    }

    builder(node) {
        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: "Window", socket: anySocket}],
            [{name: "Array", socket: anySocket}],
            []);
    }
}
