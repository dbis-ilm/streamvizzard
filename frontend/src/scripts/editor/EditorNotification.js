import TemplateHost from "@/scripts/tools/TemplateHost";

export default class EditorNotification extends TemplateHost {
    /** @param {String} content
     * @param {Number} posX
     * @param {Number} posY
     * @param {Number} duration */
    constructor(content, posX, posY, duration = 1500) {
        super();

        this.content = content;
        this.duration = duration;
        this.posX = posX;
        this.posY = posY;
    }
}