export function fitViewport([x, y], element) {
    return [
        Math.min(x, window.innerWidth - element.clientWidth),
        Math.min(y, window.innerHeight - element.clientHeight)
    ]
}

export default function debounce(next, ms) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            next(...args);
        }, ms);
    };
}