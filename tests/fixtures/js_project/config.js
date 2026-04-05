/**
 * Application configuration.
 * 
 * The Modernizer agent should convert this to TypeScript with typed config.
 */

const config = {
    apiUrl: "https://api.example.com",
    timeout: 5000,
    retries: 3,
    debug: false,
    
    features: {
        darkMode: true,
        notifications: true,
        analytics: false,
    },
    
    pagination: {
        defaultPageSize: 20,
        maxPageSize: 100,
    },
};

function getConfig(key) {
    return config[key];
}

function setConfig(key, value) {
    config[key] = value;
}

function isFeatureEnabled(featureName) {
    return config.features && config.features[featureName] === true;
}

module.exports = {
    config,
    getConfig,
    setConfig,
    isFeatureEnabled,
};
