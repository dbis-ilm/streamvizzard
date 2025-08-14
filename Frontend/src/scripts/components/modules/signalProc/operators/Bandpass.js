import {Component} from "@/scripts/components/Component";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {Display} from "@/scripts/components/monitor/Display";
import {signalSocket} from "@/scripts/components/modules/signalProc";

export default class _Bandpass extends Component {
    constructor(pathIdentifier){
        super("Bandpass", "Bandpass", pathIdentifier);
    }

    builder(node) {
        node.threshold1 = new NumControl(node, 'thres1', false, 100, "Threshold 1", "", 1);
        node.threshold2 = new NumControl(node, 'thres2', false, 200, "Threshold 2", "", 1);
        node.order= new NumControl(node, 'order', false, 3, "Order", "", 1);

        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: signalSocket.name, socket: signalSocket}],
            [{name: signalSocket.name, socket: signalSocket}],
            [node.threshold1, node.threshold2, node.order]);
    }

    getData(node) {
        return {
            threshold1: node.threshold1.getValue(),
            threshold2: node.threshold2.getValue(),
            order: node.order.getValue()
        }
    }

    setData(node, data) {
        node.threshold1.setValue(data.threshold1);
        node.threshold2.setValue(data.threshold2);
        node.order.setValue(data.order);
    }
}
