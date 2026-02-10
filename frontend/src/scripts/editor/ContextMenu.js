import {SvInstance} from "@/scripts/StreamVizzard";
import {v4} from "uuid";
import {MODALS} from "@/scripts/interface/Interface";

export class ContextMenu {
    constructor(showSearchbar, posX, posY) {
        this.id = v4(); // Uniquely identify menu for re-creation

        this.showSearchbar = showSearchbar;
        this.delay = 50;

        this.items = []; // [name, func, path]

        this.posX = posX;
        this.posY = posY;
    }

    _addItem(name, func, path=null) {
        this.items.push([name, func, path != null ? path : []]);
    }
}

export class MainContextMenu extends ContextMenu {
    /** @param {number} posX
     * @param {number} posY
     * @param {Object} [options]
     * @param {number|null} [options.forceId]
     * @param {Object|null} [options.forcePos]
     * @param {Function|null} [options.preCreatedCb]
     * @param {Function|null} [options.postCreatedCb]
     */
    constructor(posX, posY, {
        forceId = null, forcePos = null,
        preCreatedCb = null, postCreatedCb = null} = {}) {

        super(true, posX, posY);

        let createPos = forcePos != null ? forcePos : SvInstance.editor.getEditorPos({x: posX, y: posY});

        for(const definition of SvInstance.modules.opDefinitions) {
            const path = definition.contextPath;

            if (Array.isArray(path)) { // add to the menu if path is an array
                this._addItem(definition.displayName, async () => {
                    if(preCreatedCb != null) preCreatedCb(definition);

                    let op = await SvInstance.pipeline.createOperator(definition, {id: forceId, x: createPos.x, y: createPos.y});

                    if(postCreatedCb != null) postCreatedCb(op);
                }, path);
            }
        }
    }
}

export class OperatorContextMenu extends ContextMenu {
    /** @param {number} posX
     * @param {number} posY
     * @param {SvOperator} operator **/
    constructor(posX, posY, operator) {
        super(false, posX, posY);

        this.operator = operator;

        this._addItem("Duplicate", async () => {
            let sd = this.operator.exportSaveData();

            sd["posX"] = operator.posX + 25;
            sd["posY"] = operator.posY + 25;

            let op = await SvInstance.pipeline.createOperatorFromSaveData(sd, false);

            SvInstance.editor.selectOperator(op);
        });

        this._addItem("Replace", () => {
            // Save connection data to restore
            let conSaveData = [];

            for(let socket of [...operator.inputs].concat([...operator.outputs])) {
                for(let con of socket.connections) conSaveData.push(con.exportSaveData());
            }

            let compileSaveData = operator.compiler.exportSaveData();

            let preCreate = function() {
                // Remove old operator
                SvInstance.pipeline.deleteOperator(operator);
            };

            /** @param {SvOperator} newOp **/
            let postCreated = (newOp) => {
                newOp.uuid = operator.uuid;
                newOp.compiler.importSaveData(compileSaveData);

                // Only keep name if it's not the default operator name

                if(operator.name !== operator.definition.displayName) newOp.name = operator.name;

                // Re-Create connections

                for(let conData of conSaveData) SvInstance.pipeline.createConnectionFromSaveData(conData, true);
            };

            let forcePos = {x: operator.posX, y: operator.posY};

            SvInstance.editor.openMainContextMenu(posX, posY,
                {forceId: operator.id, forcePos, preCreatedCb: preCreate, postCreatedCb: postCreated});
        });

        if(operator.group == null) {
            this._addItem("Group", () => { SvInstance.pipeline.createGroup(operator); });
        }

        if(operator.group != null) {
            this._addItem("Ungroup", () => { operator.group.removeOperator(operator); });
        }

        this._addItem("Store Preset", () => {
            SvInstance.interface.openModal(MODALS.OP_PRESET_STORE, operator);
        });
    }
}