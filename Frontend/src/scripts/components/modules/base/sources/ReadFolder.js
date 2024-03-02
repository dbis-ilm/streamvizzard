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
        node.repeatCtrl  = new BoolControl(node, 'boolCtrl', false, 'Loop',
            'Repeats from the start when reaching end of file');
        node.srcCtrl = new StringControl(node, 'srcCtr', false, 'C:/Users/Timo/Downloads/dummySensor.txt');
        node.rate = new NumControl(node, 'rate', false, 5, "Rate",
            "How many lines per second are processed", 0)

        return this.onBuilderInitialized(node,
            new Display(node, STRING_DT.name),
            [],
            [{name: "Line", socket: strSocket}],
            [node.repeatCtrl, node.srcCtrl, node.rate]);
    }

    getData(node) {
        return {
            path: node.srcCtrl.getValue(),
            repeat: node.repeatCtrl.getValue() ? 1 : 0,
            rate: node.rate.getValue()
        }
    }

    setData(node, data) {
        node.srcCtrl.setValue(data.path);
        node.repeatCtrl.setValue(data.repeat === 1);
        node.rate.setValue(data.rate);
    }
}
