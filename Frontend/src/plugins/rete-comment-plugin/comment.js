import Draggable from './draggable';
import Vue from "vue";
import FrameTemplate from "@/plugins/rete-comment-plugin/FrameTemplate";

export default class Comment {
    constructor(text, editor) {
        this.editor = editor;
        this.text = text;
        this.scale = 1;
        this.x = 0;
        this.y = 0;
        this.dragPosition = [0, 0];
        this.links = [];

        this.initView();
        this.update();
    }

    initView() {
        const componentClass = Vue.extend(FrameTemplate);
        const instance = new componentClass({
            propsData: {frame: this}
        });

        instance.$mount();

        this.instance = instance;

        this.el = instance.$el;
        this.el.tabIndex = 1;
        this.el.addEventListener('contextmenu', this.onContextMenu.bind(this));
        this.el.addEventListener('focus', this.onFocus.bind(this));
        this.el.addEventListener('blur', this.onBlur.bind(this));

        this.draggable = new Draggable(this.el, () => this.onStart(), (dx, dy) => this.onTranslate(dx, dy));
    }

    linkTo(ids) {
        this.links = ids || [];
    }

    linkedTo(node) {
        return this.links.includes(node.id);
    }

    k() {
        return 1;
    }

    onContextMenu(e) {
        e.preventDefault();
        e.stopPropagation();

        //this.editor.trigger('editcomment', this);
    }

    onFocus() {
        this.scale = Math.max(1, 1 / this.k());
        this.update();
        this.editor.trigger('commentselected', this)
    }

    focused() {
        return document.activeElement === this.el;
    }

    onBlur() {
        this.scale = 1;
        this.update()
    }

    blur() {
        this.el.blur();
    }

    onStart() {
        this.dragPosition = [this.x, this.y];

        this.editor.trigger("commentMoveStart", this);
    }

    translate(x, y) {
        let prev = [this.x, this.y];
        let comment = this;

        this.x = x;
        this.y = y;

        this.update();

        this.editor.trigger("commentMoved", {comment, prev});
    }

    onTranslate (dx, dy) { //For dragging
        let prev = [this.x, this.y];
        let comment = this;

        const [x, y] = this.dragPosition;

        this.x = x + this.scale * dx;
        this.y = y + this.scale * dy;

        this.update();

        this.editor.trigger("commentMoved", {comment, prev});
    }

    update() {
        this.el.style.transform = `translate(${this.x}px, ${this.y}px) scale(${this.scale})`;
    }

    getID() {
        return this.instance._uid; //Vue's unique identifier
    }

    updateID(id) {
        this.instance._uid = id;
    }

    toJSON() {
        return {
            text: this.text,
            position: [ this.x, this.y ],
            links: this.links
        }
    }

    destroy() {
        this.draggable.destroy();
    }
}
