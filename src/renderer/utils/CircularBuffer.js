import { isInt, mod } from './index';

// Max array size: https://stackoverflow.com/questions/6154989/maximum-size-of-an-array-in-javascript
const MAX_SIZE = Math.min(Number.MAX_SAFE_INTEGER, 2 ** 32 - 1);
export { MAX_SIZE };

export default function createCircularBuffer(size) {
    if (!isInt(size)) {
        throw new TypeError('createCircularBuffer: size must be an integer.');
    }

    if (size <= 0 || size > MAX_SIZE) {
        throw new RangeError(`createCircularBuffer: size out of bounds: (0, ${MAX_SIZE}]`);
    }

    const items = Array(size);
    let fill = 0;
    let next = 0;

    function push(item) {
        items[next] = item;
        fill = Math.min(size, fill + 1);
        next = next === size - 1 ? 0 : next + 1;
    }

    function get(index) {
        if (!isInt(index)) {
            throw new TypeError('CircularBuffer.get: index must be an integer.');
        }

        if (index < -fill || index >= fill) {
            throw new RangeError(`CircularBuffer.get: index out of bounds: [${-fill}, ${fill}).`);
        }

        return items[mod(next + index, fill)];
    }

    function reset() {
        fill = 0;
        next = 0;
    }

    function toList() {
        const ret = items.slice(0, next);

        if (fill === size) {
            ret.unshift(...items.slice(next, size));
        }

        return ret;
    }

    return Object.create(null, {
        size: {
            enumerable: true,
            get() {
                return size;
            },
        },
        fill: {
            enumerable: true,
            get() {
                return fill;
            },
        },
        next: {
            enumerable: true,
            get() {
                return next;
            },
        },
        push: { value: push },
        get: { value: get },
        reset: { value: reset },
        toList: { value: toList },
    });
}
