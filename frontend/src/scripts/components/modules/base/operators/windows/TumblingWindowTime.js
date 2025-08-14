import {Component} from "@/scripts/components/Component";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";

export default class _TumblingWindowTime extends Component {
    constructor(pathIdentifier){
        super("TumblingWindowTime", "Tumb. Window Time", pathIdentifier);
    }

    builder(node) {
        node.value = new NumControl(node, 'value', false, '5', 'Interval',
            'The window will evaluate every x seconds and send all collected tuples', 0);

        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: "Any", socket: anySocket}],
            [{name: "Window", socket: anySocket}], //TODO: DATATYPE FOR ARRAY?
            [node.value]);
    }
}
