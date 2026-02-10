import {Definition} from "@/scripts/pipeline/operators/Definition";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SelectParam} from "@/scripts/pipeline/operators/modules/base/params/SelectParam";
import {STRING_DT, strSocket} from "@/scripts/pipeline/operators/modules/base";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _KafkaSource extends Definition {
    constructor(pathIdentifier){
        super("KafkaSource", "Kafka Source", pathIdentifier);
    }

    build(operator) {
        let broker = new StringParam("broker", "127.0.0.1", "Broker");
        let port = new NumberParam("port", 9092, 0, null, "Port","The port used for the kafka connection");
        let topic = new StringParam("topic", "my-topic", "Topic");
        let groupID = new StringParam("groupID", "my-group", "GroupID");
        let offset = new SelectParam("offset",
            [{title: "Earliest", key: "earliest"}, {title: "Latest", key: "latest"}], "latest", "Offset",
            "Latest, if only produced messages should be processed after the source started, earliest, if also past data should be received.");
        let encoding = new StringParam("encoding", "utf-8", "Encoding", "Encoding used to decode the received bytes");

        this._construct(operator,
            [],
            [new SocketDef(strSocket, "Data")],
            [broker, port, topic, groupID, offset, encoding], STRING_DT);
    }
}
