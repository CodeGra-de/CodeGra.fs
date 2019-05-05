export function isInt(x) {
    return x === parseInt(x, 10);
}

export function mod(a, b) {
    if (!Number.isFinite(a) || !Number.isFinite(b)) {
        throw new TypeError('mod: arguments must be Numbers.');
    }

    if (b === 0) {
        throw new RangeError('mod: modulus cannot be zero.');
    }

    let ret = a % b;

    if (ret < 0) {
        ret += b < 0 ? -b : b;
    }

    return ret;
}

const uniq = (function IIFE() {
    let i = 0;

    return function uniq() {
        return i++;
    };
}());
export { uniq };

export function isEqual(a, b) {
    if (typeof a !== 'object' || typeof b !== 'object') {
        throw new TypeError('isEqual: arguments must be of type "object".');
    }

    const bKeys = new Set(Object.keys(b));
    for (const key of Object.keys(a)) {
        if (!bKeys.delete(key) || a[key] !== b[key]) {
            return false;
        }
    }
    return bKeys.size === 0;
}

// https://stackoverflow.com/questions/13405129/javascript-create-and-save-file
export function downloadFile(data, filename, type) {
    const file = new Blob([data], { type });
    if (window.navigator.msSaveOrOpenBlob) {
        // IE10+
        window.navigator.msSaveOrOpenBlob(file, filename);
    } else {
        const url = URL.createObjectURL(file);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 0);
    }
}
