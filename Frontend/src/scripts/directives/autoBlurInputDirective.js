// Blurs the input element after an input event
// Tested with: v-select

export default {
    bind(el, binding, vNode) {
        // Access the Vue component instance
        const element = vNode.componentInstance;

        if (element) {
            element.$on(["input", "change", "close"], () => {
                // Schedule blur for next tick to allow other event-listeners to response to input
                element.$nextTick(function () {
                    el.querySelector('input').blur();
                });
            });
        }
    },
};