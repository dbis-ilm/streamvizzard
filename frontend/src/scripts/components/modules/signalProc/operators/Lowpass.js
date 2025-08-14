import {Component} from "@/scripts/components/Component";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {Display} from "@/scripts/components/monitor/Display";
import {signalSocket} from "@/scripts/components/modules/signalProc";

export default class _Lowpass extends Component {
    constructor(pathIdentifier){
        super("Lowpass", "Lowpass", pathIdentifier);
    }

    builder(node) {
        node.threshold= new NumControl(node, 'thres', false, 100, "Threshold", "", 1);
        node.order= new NumControl(node, 'order', false, 3, "Order", "", 1);

        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: signalSocket.name, socket: signalSocket}],
            [{name: signalSocket.name, socket: signalSocket}],
            [node.threshold, node.order]);
    }

    getData(node) {
        return {
            threshold: node.threshold.getValue(),
            order: node.order.getValue()
        }
    }

    setData(node, data) {
        node.threshold.setValue(data.threshold);
        node.order.setValue(data.order);
    }
}
