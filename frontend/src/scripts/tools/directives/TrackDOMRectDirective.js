// expects a ViewRect value as binding

export default {
    // Use inserted instead of bind to ensure the elm is already added to the DOM so we can calculate an initial size!
    inserted(el, binding) {
        function updateRect() {
            let r = el.getBoundingClientRect();

            binding.value.left = r.x;
            binding.value.top = r.y;
            binding.value.width = r.width;
            binding.value.height = r.height;
        }

        const ro = new ResizeObserver(updateRect);

        el._resizeObserver = ro;
        ro.observe(el);

        updateRect(); // Initial size calculation
    },

    unbind(el) {
        el._resizeObserver?.disconnect()
        delete el._resizeObserver
    }
}