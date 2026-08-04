/**
 * Toggle a value in an array. If the value exists, remove it; otherwise, add it.
 * @param items The array to mutate.
 * @param value The value to toggle.
 */
export const toggleValue = <T,>(items: T[], value: T): void => {
    const index = items.indexOf(value);
    if (index >= 0) items.splice(index, 1);
    else items.push(value);
};