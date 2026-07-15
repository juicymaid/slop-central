try {
  delete globalThis.navigator;
  delete global.navigator;
  delete globalThis.localStorage;
  delete global.localStorage;
} catch (e) {}

const mockLocalStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
  clear: () => {}
};
globalThis.localStorage = mockLocalStorage;
global.localStorage = mockLocalStorage;
console.log("Mocked localStorage and navigator successfully.");
