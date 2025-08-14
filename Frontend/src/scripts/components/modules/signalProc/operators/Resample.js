import {Component} from "@/scripts/components/Component";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {Display} from "@/scripts/components/monitor/Display";
import {signalSocket} from "@/scripts/components/modules/signalProc";

export default class _Resample extends Component {
    constructor(pathIdentifier){
        super("Resample", "Resample", pathIdentifier);
    }

    builder(node) {
        node.sampleRate= new NumControl(node, 'sr', false, 16000, "Sample Rate", "", 1);

        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: signalSocket.name, socket: signalSocket}],
            [{name: signalSocket.name, socket: signalSocket}],
            [node.sampleRate]);
    }

    getData(node) {
        return {
            sampleRate: node.sampleRate.getValue()
        }
    }

    setData(node, data) {
        node.sampleRate.setValue(data.sampleRate);
    }
}
