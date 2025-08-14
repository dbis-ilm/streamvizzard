import { createNode, traverse } from './utils';
import Menu from './menu/index';

export default class MainMenu extends Menu {
    constructor(editor, props, vueComponent, { items, allocate, rename, nodeCreatedCallback }) {
        super(editor, props, vueComponent);

        const createPos = editor.view.area.mouse;

        for(const component of editor.components.values()) {
            const path = allocate(component);
    
            if (Array.isArray(path)) { // add to the menu if path is array
                this.addItem(rename(component), async () => {
                    let newNode = await createNode(component, createPos);
                    editor.addNode(newNode);

                    if(nodeCreatedCallback != null) nodeCreatedCallback(newNode);
                }, path);
            }
        }
    
        traverse(items, (name, func, path) => this.addItem(name, func, path))
    }
}