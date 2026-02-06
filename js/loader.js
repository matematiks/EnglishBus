export const Loader = {
    show() {
        // Try to find the global loader
        const loader = document.getElementById('global-loader');
        if (loader) {
            loader.classList.remove('hidden');
        } else {
            console.warn("Loader element not found");
        }
    },

    hide() {
        const loader = document.getElementById('global-loader');
        if (loader) {
            loader.classList.add('hidden');
        }
    }
};
