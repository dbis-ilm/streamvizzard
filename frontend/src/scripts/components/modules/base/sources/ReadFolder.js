import {Component} from "@/scripts/components/Component";
import {BoolControl} from "@/scripts/components/modules/base/controls/BoolCtrl";
import {STRING_DT, strSocket} from "@/scripts/components/modules/base";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {Display} from "@/scripts/components/monitor/Display";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";

export default class _ReadFolder extends Component {
    constructor(pathIdentifier){
        super("ReadFolder", "Read Folder", pathIdentifier, true);
    }

    builder(node) {
        node.repeat  = new BoolControl(node, 'repeat', false, 'Loop',
            'Repeats from the start when reaching end of file');
        node.path = new StringControl(node, 'path', false, '', "Path", "Source folder to read files from, ordered by modification date");
        node.limitRate = new BoolControl(node, 'limitRate', false, 'Limit Rate',
            'If the source should produce tuples in a fixed rate', true);
        node.rate = new NumControl(node, 'rate', false, 30, "Rate",
            "How many lines per second are processed", 0);

        node.limitRate.onChangeCallback = (val) => {
            node.rate.show = val;
        };

        return this.onBuilderInitialized(node,
            new Display(node, STRING_DT.name),
            [],
            [{name: "Line", socket: strSocket}],
            [node.repeat, node.path, node.limitRate, node.rate]);
    }
}
