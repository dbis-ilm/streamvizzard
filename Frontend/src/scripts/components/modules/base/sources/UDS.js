import {Component} from "@/scripts/components/Component";
import {STRING_DT} from "@/scripts/components/modules/base";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";
import {CodeControl} from "@/scripts/components/modules/base/controls/CodeCtrl";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";

export default class _UDS extends Component {
    constructor(pathIdentifier){
        super("UDS", "UDS", pathIdentifier, true);
    }

    builder(node) {
        node.outCount = new NumControl(node, "outCount", false, 1, "Outputs", "", 1);
        node.code = new CodeControl(node, 'code', false, "class UserDefinedSource:\n" +
            "    def onStart(self):\n" +
            "        ...\n\n" +
            "    def runLoop(self) -> tuple:\n" +
            "        ...\n\n" +
            "    def onDestroy(self):\n" +
            "        ...");

        return this.onBuilderInitialized(node,
            new Display(node, STRING_DT.name),
            [],
            [{name: anySocket.name, socket: anySocket}],
            [node.outCount, node.code]);
    }

    onControlValueChanged(ctrl, node, oldVal) {
        // First update sockets & connections (which triggers connection removed)
        if(ctrl === node.outCount) this.updateSockets(node, 0, node.outCount.getValue(), anySocket, anySocket).then();

        // Then, send update info to server
        super.onControlValueChanged(ctrl, node, oldVal);
    }

    getData(node) {
        return {
            code: node.code.getValue(),
            outputs: node.outCount.getValue()
        }
    }

    async setData(node, data) {
        node.code.setValue(data.code);
        node.outCount.setValue(data.outputs);

        await this.updateSockets(node, 0, node.outCount.getValue(), anySocket, anySocket).then();
    }
}
