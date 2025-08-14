import {Component} from "@/scripts/components/Component";
import {STRING_DT} from "@/scripts/components/modules/base";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {Display} from "@/scripts/components/monitor/Display";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {anySocket} from "@/scripts/components/modules";

export default class _SocketTextSource extends Component {
    constructor(pathIdentifier){
        super("SocketTextSSource", "Socket Text Server Source", pathIdentifier, true);
    }

    builder(node) {
        node.ip = new StringControl(node, 'ip', false, '127.0.0.1', "Host");
        node.port = new NumControl(node, 'port', false, 9000, "Port","The port used for the socket connection", 0);
        node.delimiter = new StringControl(node, 'delimiter', false, "\\n", "Delimiter", "The delimiter used to differentiate between received data elements");
        node.encoding = new StringControl(node, 'encoding', false, "utf-8", "Encoding", "The encoding used to translate the received bytes to text");

        return this.onBuilderInitialized(node,
            new Display(node, STRING_DT.name),
            [],
            [{name: "Data", socket: anySocket}],
            [node.ip, node.port, node.delimiter, node.encoding]);
    }
}
