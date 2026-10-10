/** HbA1c is always shown with one decimal place (JSON drops trailing zeros: 6.0 arrives as 6). */
export const formatHbA1c = (value: number) => `${value.toFixed(1)}%`;
