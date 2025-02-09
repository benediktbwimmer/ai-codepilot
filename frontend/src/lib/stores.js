import { writable } from 'svelte/store';

function createPersistentStore(key, initialValue) {
    // Load initial state from localStorage
    let initial;
    try {
        const storedValue = localStorage.getItem(key);
        initial = storedValue ? JSON.parse(storedValue) : initialValue;
    } catch (error) {
        initial = initialValue;
    }
    
    const store = writable(initial);
    
    // Subscribe to changes and update localStorage
    store.subscribe(value => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            // Silently handle storage errors
        }
    });
    
    return store;
}

// Form state store
export const formState = createPersistentStore('formState', {
    userRequest: '',
    review: true,
    max_iterations: 2,
    rootDirectory: '.'
});

// Messages store
export const messagesState = createPersistentStore('messagesState', {
    messages: [],
    currentDiff: ''
});