import {Component} from "@/scripts/components/Component";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {Display} from "@/scripts/components/monitor/Display";
import {SIGNAL_DT, signalSocket} from "@/scripts/components/modules/signalProc";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {BoolControl} from "@/scripts/components/modules/base/controls/BoolCtrl";

export default class _AudioFile extends Component {
    constructor(pathIdentifier){
        super("AudioFile", "Audio File", pathIdentifier, true);
    }

    builder(node) {
        node.path = new StringControl(node, 'path', false, '', "Source");
        node.rate = new NumControl(node, 'rate', false, 44100, "Sample Rate", "", 1);
        node.repeat = new BoolControl(node, 'repeat', false, 'Loop',
            'Repeats from the start when reaching end of file', false);

        return this.onBuilderInitialized(node,
            new Display(node, SIGNAL_DT.name),
            [],
            [{name: signalSocket.name, socket: signalSocket}],
            [node.path, node.rate, node.repeat]);
    }
}
