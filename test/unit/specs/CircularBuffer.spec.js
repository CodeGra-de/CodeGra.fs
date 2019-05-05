import createCircularBuffer, { MAX_SIZE } from '../../../src/renderer/utils/CircularBuffer';
import { randomNumbers, randomInts, nonInts } from '../utils';

const TEST_SIZE = 20;

describe('createCircularBuffer()', () => {
    it('should throw a TypeError when size is not an integer', () => {
        for (const size of nonInts) {
            expect(() => {
                createCircularBuffer(size);
            }).to.throw(TypeError);
        }
    });

    it('should throw a RangeError when size is zero', () => {
        expect(() => {
            createCircularBuffer(0);
        }).to.throw(RangeError);
    });

    it('should throw a RangeError when size is negative', () => {
        for (const size of randomInts(-MAX_SIZE, 0, TEST_SIZE)) {
            expect(() => {
                createCircularBuffer(size);
            }).to.throw(RangeError);
        }
    });

    it('should throw a RangeError when size is greater than MAX_SIZE', () => {
        for (const size of randomInts(MAX_SIZE + 1, 2 * MAX_SIZE, TEST_SIZE)) {
            expect(() => {
                createCircularBuffer(size);
            }).to.throw(RangeError);
        }
    });

    it('should succeed when size is within bounds', () => {
        for (const size of randomInts(0, MAX_SIZE + 1, TEST_SIZE)) {
            expect(createCircularBuffer(size)).to.have.property('size', size);
        }
    });
});

describe('CircularBuffer', () => {
    let bufs;

    beforeEach(() => {
        // Some of the tests require a size of at least 2,
        // because they partially fill the buffer.
        bufs = randomInts(2, 1024, TEST_SIZE).map(
            size => [createCircularBuffer(size), size],
        );
    });

    it('should not have an items property', () => {
        for (const [buf, size] of bufs) {
            expect(buf).not.to.have.ownPropertyDescriptor('items');
        }
    });

    describe('.size', () => {
        it('should not be writable', () => {
            for (const [buf, size] of bufs) {
                expect(() => {
                    buf.size = 0;
                }).to.throw(TypeError);
            }
        });

        it('should initially be equal to the given size', () => {
            for (const [buf, size] of bufs) {
                expect(buf.size).to.equal(size);
            }
        });

        it('should not change when the buffer is filled', () => {
            for (const [buf, size] of bufs) {
                for (let i = 0; i < 1.5 * size; i++) {
                    buf.push(i);
                    expect(buf.size).to.equal(size);
                }
            }
        });
    });

    describe('.fill', () => {
        it('should not be writable', () => {
            for (const [buf, size] of bufs) {
                expect(() => {
                    buf.fill = 0;
                }).to.throw(TypeError);
            }
        });

        it('should initially be 0', () => {
            for (const [buf, size] of bufs) {
                expect(buf.fill).to.equal(0);
            }
        });

        it('should grow as the buffer is filled', () => {
            for (const [buf, size] of bufs) {
                for (let i = 1; i < size / 2; i++) {
                    buf.push(i);
                    expect(buf.fill).to.equal(i);
                }
            }
        });

        it('should not exceed the buffer size', () => {
            for (const [buf, size] of bufs) {
                for (let i = 1; i < size * 1.5; i++) {
                    buf.push(i);
                    expect(buf.fill).to.equal(Math.min(i, size));
                }
            }
        });
    });

    describe('.next', () => {
        it('should not be writable', () => {
            for (const [buf, size] of bufs) {
                expect(() => {
                    buf.next = 0;
                }).to.throw(TypeError);
            }
        });

        it('should initially be 0', () => {
            for (const [buf, size] of bufs) {
                expect(buf.next).to.equal(0);
            }
        });

        it('should grow as the buffer is filled', () => {
            for (const [buf, size] of bufs) {
                for (let i = 1; i < size / 2; i++) {
                    buf.push(i);
                    expect(buf.next).to.equal(i);
                }
            }
        });

        it('should wrap around when the buffer is full', () => {
            for (const [buf, size] of bufs) {
                for (let i = 1; i < size * 1.5; i++) {
                    buf.push(i);
                    expect(buf.next).to.equal(i % size);
                }
            }
        });
    });

    describe('.push()', () => {
        it('should add items to the end of the list', () => {
            for (const [buf, size] of bufs) {
                for (const x of randomInts(0, 1024, TEST_SIZE)) {
                    buf.push(x);
                    expect(buf.get(-1)).to.equal(x);
                }
            }
        });

        it('should never push past the given size', () => {
            for (const [buf, size] of bufs) {
                for (let i = 1; i < 1.5 * size; i++) {
                    buf.push(i);
                    expect(buf.fill).to.be.at.most(size);
                }
            }
        });
    });

    describe('.get()', () => {
        it('should throw a TypeError when index is not an integer', () => {
            for (const [buf, size] of bufs) {
                for (const index of nonInts) {
                    expect(() => {
                        buf.get(index);
                    }).to.throw(TypeError);
                }
            }
        });

        it('should throw a RangeError when the buffer is empty', () => {
            for (const [buf, size] of bufs) {
                for (const index of [0, 1, size - 1, -1, -size]) {
                    expect(() => {
                        buf.get(index);
                    }).to.throw(RangeError);
                }
            }
        });

        describe('when the buffer is partially filled', () => {
            let fills;

            beforeEach(() => {
                fills = bufs.map(([buf, size]) => {
                    const fill = randomInts(1, size, 1)[0];

                    for (let i = 0; i < fill; i++) {
                        buf.push(i);
                    }

                    return [buf, size, fill];
                });
            });

            it('should throw a RangeError when index is out of bounds', () => {
                for (const [buf, size, fill] of fills) {
                    for (const index of randomInts(fill, MAX_SIZE, TEST_SIZE)) {
                        expect(() => {
                            buf.get(index);
                        }).to.throw(RangeError);
                    }
                    for (const index of randomInts(-MAX_SIZE, -fill - 1, TEST_SIZE)) {
                        expect(() => {
                            buf.get(index);
                        }).to.throw(RangeError);
                    }
                }
            });

            it('should get the expected item when index is within bounds', () => {
                for (const [buf, size, fill] of fills) {
                    for (const index of randomInts(-fill, fill - 1, TEST_SIZE)) {
                        const expected = index < 0 ? index + fill : index;
                        expect(buf.get(index)).to.equal(expected);
                    }
                }
            });
        });
    });

    describe('.reset()', () => {
        it('should reset the buffer size and position', () => {
            for (const [buf, size] of bufs) {
                const n = randomInts(1, size, 1)[0];

                for (let i = 0; i < n; i++) {
                    buf.push(i);
                }

                expect(buf.fill).not.to.equal(0);

                buf.reset();

                expect(buf.fill).to.equal(0);
                expect(buf.next).to.equal(0);
                expect(() => {
                    buf.get(0);
                }).to.throw(RangeError);
            }
        });
    });

    describe('.toList()', () => {
        it('should return an empty list if the buffer is empty', () => {
            for (const [buf, size] of bufs) {
                const list = buf.toList();

                expect(list).to.be.instanceof(Array);
                expect(list).to.be.empty;
            }
        });

        it('should return the input list if it is smaller than the buffer', () => {
            for (const [buf, size] of bufs) {
                const values = randomNumbers(0, 10, Math.floor(0.99 * Math.random() * size));

                for (const x of values) {
                    buf.push(x);
                }

                const list = buf.toList();

                expect(list).to.eql(values);
            }
        });

        it('should return the tail of the input list if it is larger than the buffer', () => {
            for (const [buf, size] of bufs) {
                const values = randomNumbers(0, 10, size + Math.floor(0.99 * Math.random() * size));

                for (const x of values) {
                    buf.push(x);
                }

                const list = buf.toList();

                expect(list).to.have.lengthOf(size);
                expect(list).to.be.eql(values.slice(-size));
            }
        });
    });
});
