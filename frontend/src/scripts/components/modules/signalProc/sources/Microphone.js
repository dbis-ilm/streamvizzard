import {Component} from "@/scripts/components/Component";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {Display} from "@/scripts/components/monitor/Display";
import {SIGNAL_DT, signalSocket} from "@/scripts/components/modules/signalProc";

export default class _Microphone extends Component {
    constructor(pathIdentifier){
        super("Microphone", "Microphone", pathIdentifier, true);
    }

    builder(node) {
        node.rate = new NumControl(node, 'rate', false, 44100, "Rate", "", 1)

        return this.onBuilderInitialized(node,
            new Display(node, SIGNAL_DT.name),
            [],
            [{name: signalSocket.name, socket: signalSocket}],
            [node.rate]);
    }

    getData(node) {
        return {
            rate: node.rate.getValue()
        }
    }

    setData(node, data) {
        node.rate.setValue(data.rate);
    }
}
