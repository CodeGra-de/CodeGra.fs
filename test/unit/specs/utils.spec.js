import { isInt, mod, uniq } from '../../../src/renderer/utils';
import { randomInts, nonNumbers, nonInts, zip } from '../utils';

const TEST_SIZE = 1000;

describe('isInt()', () => {
    it('should return false when passed something other than an integer', () => {
        for (const x of nonInts) {
            expect(isInt(x)).to.be.false;
        }
    });

    it('should return true when passed an integer', () => {
        const values = randomInts(
            -Number.MAX_SAFE_INTEGER / 2,
            Number.MAX_SAFE_INTEGER / 2,
            TEST_SIZE,
        );

        for (const x of values) {
            expect(isInt(x)).to.be.true;
        }
    });
});

describe('mod()', () => {
    function naiveMod(a, b) {
        b = Math.abs(b);

        while (a < 0) a += b;
        while (a >= b) a -= b;

        return a;
    }

    it('should throw a TypeError if a single argument is given', () => {
        expect(() => {
            mod(1);
        }).to.throw(TypeError);

        for (const x of nonNumbers) {
            expect(() => {
                mod(x);
            }).to.throw(TypeError);
        }
    });

    it('should throw a TypeError if the first argument is not a number', () => {
        for (const x of nonNumbers) {
            expect(() => {
                mod(x, 1);
            }).to.throw(TypeError);
        }
    });

    it('should throw a TypeError if the second argument is not a number', () => {
        for (const x of nonNumbers) {
            expect(() => {
                mod(1, x);
            }).to.throw(TypeError);
        }
    });

    it('should throw a TypeError if neither argument is a number', () => {
        for (const x of nonNumbers) {
            expect(() => {
                mod(x, x);
            }).to.throw(TypeError);
        }
    });

    it('should throw a RangeError if modulus is zero', () => {
        const values = randomInts(
            -Number.MAX_SAFE_INTEGER / 2,
            Number.MAX_SAFE_INTEGER / 2,
            TEST_SIZE,
        );

        for (const a of values) {
            expect(() => {
                mod(a, 0);
            }).to.throw(RangeError);
        }
    });

    it('should return 0 when the arguments are equal', () => {
        const values = randomInts(
            -Number.MAX_SAFE_INTEGER / 2,
            Number.MAX_SAFE_INTEGER / 2,
            TEST_SIZE,
        );

        for (const a of values) {
            expect(mod(a, a)).to.equal(0);
        }
    });

    it('should return a number in the range[0, |b|)', () => {
        const values = zip(
            randomInts(-Number.MAX_SAFE_INTEGER / 2, Number.MAX_SAFE_INTEGER / 2, TEST_SIZE),
            randomInts(-Number.MAX_SAFE_INTEGER / 2, Number.MAX_SAFE_INTEGER / 2, TEST_SIZE),
        );

        for (const [a, b] of values) {
            if (b === 0) {
                return;
            }

            const ret = mod(a, b);

            expect(ret).to.equal(naiveMod(a, b));
            expect(ret).to.be.at.least(0);
            expect(ret).to.be.below(Math.abs(b));
        }
    });
});

describe('uniq()', () => {
    it('should generate a large number of unique items', () => {
        const items = new Set();
        const n = TEST_SIZE ** 2;

        for (let i = 0; i < n; i++) {
            items.add(uniq());
        }

        expect(items.size).to.equal(n);
    });
});
