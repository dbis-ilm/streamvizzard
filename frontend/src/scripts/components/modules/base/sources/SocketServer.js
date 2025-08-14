import {Component} from "@/scripts/components/Component";
import {STRING_DT} from "@/scripts/components/modules/base";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {Display} from "@/scripts/components/monitor/Display";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {anySocket} from "@/scripts/components/modules";

export default class _SocketServer extends Component {
    constructor(pathIdentifier){
        super("SocketServer", "Socket Server", pathIdentifier, true);
    }

    builder(node) {
        node.ip = new StringControl(node, 'ip', false, '127.0.0.1', "Host");
        node.port = new NumControl(node, 'port', false, 9000, "Port","The port used for the socket connection", 0)
        node.maxBytes = new NumControl(node, 'maxBytes', false, 1024, "Max Bytes","The maximum amount of bytes a connection can send at once", 0)

        return this.onBuilderInitialized(node,
            new Display(node, STRING_DT.name),
            [],
            [{name: "Data", socket: anySocket}],
            [node.ip, node.port, node.maxBytes]);
    }
}
