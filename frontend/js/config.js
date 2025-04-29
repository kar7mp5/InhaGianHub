const ENV = "production";  // "development" or "production"

const CONFIG = {
    development: {
        API_BASE: "http://localhost:8000"
    },
    production: {
        API_BASE: "https://your-backend.onrender.com"
    }
};

const API_BASE = CONFIG[ENV].API_BASE;
