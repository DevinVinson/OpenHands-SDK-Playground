/**
 * Utility functions for the JavaScript project.
 * 
 * The Modernizer agent should convert this to TypeScript and add types.
 */

function add(a, b) {
    return a + b;
}

function subtract(a, b) {
    return a - b;
}

function multiply(a, b) {
    return a * b;
}

function divide(a, b) {
    if (b === 0) {
        throw new Error("Cannot divide by zero");
    }
    return a / b;
}

function greet(name) {
    return `Hello, ${name}!`;
}

function greetWithTitle(name, title) {
    if (title) {
        return `Hello, ${title} ${name}!`;
    }
    return greet(name);
}

async function fetchData(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
    }
    return response.json();
}

async function postData(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });
    return response.json();
}

module.exports = {
    add,
    subtract,
    multiply,
    divide,
    greet,
    greetWithTitle,
    fetchData,
    postData,
};
