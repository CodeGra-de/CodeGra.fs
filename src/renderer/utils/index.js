const uniq = (function IIFE() {
    let i = 0;

    return function uniq() {
        return i++;
    };
}());

export { uniq };
