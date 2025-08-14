// Based on rete-auto-arrange-plugin

import ELK from 'elkjs';
import {PipelineService} from "@/scripts/services/pipelineState/PipelineService";

export class AutoLayoutPipeline {
    constructor(editor) {
        this.elk = new ELK();
        this.editor = editor;
    }

    getPortDims(socket, inSocket, index) {
        let zoom = this.editor.view.area.transform.k;
        const socketRect = socket.node.vueContext.getSocketVueContext(inSocket, socket.key).$el.getBoundingClientRect()

        // x,y relative to node, 0 works best here ...
        return {
            x: 0,
            y: index * 5, // Offset minimizes crossing edges if op has multiple ins
            width: socketRect.width / zoom,
            height: socketRect.height / zoom
        };
    }

    nodeToLayoutChild(node) {
        let zoom = this.editor.view.area.transform.k;
        const rect = node.vueContext.$el.getBoundingClientRect()

        const id = node.id;
        const width = rect.width / zoom;
        const height = rect.height / zoom;

        const inputs = Array.from(node.inputs.values());
        const outputs = Array.from(node.outputs.values());

        return {
            id,
            width,
            height,
            labels: [
                {
                    text: 'label' in node ? node.label : ''
                }
            ],
            ports: [
                ...inputs
                    .map((element, index) => {
                        const { width, height, x, y } = this.getPortDims(element, true, index);
                        const side = "WEST";

                        return {
                            id: this.getPortId(id, element.key, 'input'),
                            width,
                            height,
                            x,
                            y,
                            properties: {
                                side
                            }
                        };
                    }),
                ...outputs
                    .map((element, index) => {
                        const { width, height, x, y } = this.getPortDims(element, false, index);
                        const side = "EAST";

                        return {
                            id: this.getPortId(id, element.key, 'output'),
                            width,
                            height,
                            x,
                            y,
                            properties: {
                                side
                            }
                        };
                    })
            ],
            layoutOptions: {
                portConstraints: 'FIXED_POS'
            }
        };
    }

    connectionToLayoutEdge(connection) {
        const source = this.getPortId(connection.output.node.id, connection.output.key, 'output');
        const target = this.getPortId(connection.input.node.id, connection.input.key, 'input');

        return {
            id: connection.id,
            sources: [source],
            targets: [target]
        };
    }

    graphToElk(context) {
        const nodes = context.nodes;

        return {
            children: nodes.map(n => this.nodeToLayoutChild(n, context)),
            edges: context.connections
                .map(c => this.connectionToLayoutEdge(c))
        };
    }

    getPortId(id, key, side) {
        return [id, key, side].join('_');
    }

    async layout(props = {}) {
        const nodes = Array.from(PipelineService.getAllOperators());

        if(nodes.length === 0) return;

        const connections = Array.from(PipelineService.getAllConnections());
        const graph = {
            id: 'root',
            layoutOptions: {
                'elk.algorithm': 'layered',
                'elk.hierarchyHandling': 'INCLUDE_CHILDREN',
                'elk.edgeRouting': 'POLYLINE',
                ...props
            },
            ...this.graphToElk({ nodes, connections })
        };

        try {
            const result = await this.elk.layout(graph);

            for(let child of result.children) {
                let node = PipelineService.getOperatorByID(child.id);

                this.editor.view.nodes.get(node).translate(child.x, child.y);
                this.editor.view.updateConnections({ node });
            }
        } catch (error) {
            console.log(error);
        }
    }
}
