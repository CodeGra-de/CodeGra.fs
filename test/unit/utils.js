export function randomNumbers(a, b, n) {
    return [...Array(n).keys()].map(
        () => a + (b - a) * Math.random(),
    );
}

export function randomInts(a, b, n) {
    return randomNumbers(a, b, n).map(Math.floor);
}

export function zip(list, ...lists) {
    return list.map(
        (x, i) => [x, ...lists.map((l) => l[i])],
    );
}

export const nonNumbers = [
    undefined,
    null,
    false,
    true,
    'string',
    [],
    [1, 2, 3],
    {},
    { a: 1, b: 2 },
    new Error(),
    new (class {})(),
];

export const nonInts = [
    ...nonNumbers,
    3.14,
    Number(3.14),
    ...randomNumbers(-Number.MAX_VALUE / 2, Number.MAX_VALUE / 2, 10),
];
