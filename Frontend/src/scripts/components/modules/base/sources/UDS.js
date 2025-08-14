import {Component} from "@/scripts/components/Component";
import {STRING_DT} from "@/scripts/components/modules/base";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";
import {CodeControl} from "@/scripts/components/modules/base/controls/CodeCtrl";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";

export default class _UDS extends Component {
    constructor(pathIdentifier){
        super("UDS", "User Defined Source", pathIdentifier, true);
    }

    builder(node) {
        node.outCount = new NumControl(node, "outputs", false, 1, "Outputs", "", 1);
        node.code = new CodeControl(node, 'code', false, CodeControl.CodeType.UDO, "class UserDefinedSource:\n" +
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

    async setData(node, data) {
        await super.setData(node, data);

        await this.updateSockets(node, 0, node.outCount.getValue(), anySocket, anySocket).then();
    }
}
