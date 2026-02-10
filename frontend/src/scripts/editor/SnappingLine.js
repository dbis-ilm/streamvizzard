import TemplateHost from "@/scripts/tools/TemplateHost";

export default class SnappingLine extends TemplateHost{
    /** @param {Boolean} */ horizontal;
    /** @param {Number} */ posX;
    /** @param {Number} */ posY;
    constructor(posX, posY, horizontal) {
        super();

        this.posX = posX;
        this.posY = posY;
        this.horizontal = horizontal;
    }
}