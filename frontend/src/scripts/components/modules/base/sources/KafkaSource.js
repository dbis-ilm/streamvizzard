import {Component} from "@/scripts/components/Component";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {SelectControl} from "@/scripts/components/modules/base/controls/SelectCtrl";
import {strSocket} from "@/scripts/components/modules/base";

export default class _KafkaSource extends Component {
    constructor(pathIdentifier){
        super("KafkaSource", "Kafka Source", pathIdentifier);
    }

    builder(node) {
        node.broker = new StringControl(node, 'broker', false, '127.0.0.1', "Broker");
        node.port = new NumControl(node, 'port', false, 9092, "Port","The port used for the kafka connection", 0);
        node.topic = new StringControl(node, 'topic', false, "my-topic", "Topic");
        node.groupID = new StringControl(node, 'groupID', false, "my-group", "GroupID");
        node.offset = new SelectControl(node, 'offset',
            false, [{title: "Earliest", key: "earliest"}, {title: "Latest", key: "latest"}], "latest", "Offset",
            "Latest, if only produced messages should be processed after the source started, earliest, if also past data should be received.");
        node.encoding = new StringControl(node, 'encoding', false, 'utf-8', "Encoding", "Encoding used to decode the received bytes");

        return this.onBuilderInitialized(node,
            null,
            [],
            [{name: strSocket.name, socket: strSocket}],
            [node.broker, node.port, node.topic, node.groupID, node.offset, node.encoding]);
    }
}
