/**
 * Logger Utility - Environment-aware logging
 * 
 * Production'da debug logları disable eder, hassas bilgi sızıntısını önler.
 * Development'ta tüm logları gösterir.
 */

// Çevre tespiti (production detection)
const isProduction = () => {
    // PythonAnywhere veya production domain kontrolü
    return window.location.hostname.includes('pythonanywhere.com') ||
        window.location.hostname.includes('englishbus.com') ||
        !window.location.hostname.includes('localhost');
};

const DEBUG = !isProduction();

/**
 * Logger class - console wrapper with environment awareness
 */
export class Logger {
    constructor(context = '') {
        this.context = context;
    }

    /**
     * Debug level - sadece development'ta gösterilir
     */
    debug(...args) {
        if (DEBUG) {
            console.log(`[DEBUG]${this.context ? ` ${this.context}:` : ''}`, ...args);
        }
    }

    /**
     * Info level - önemli bilgiler
     */
    info(...args) {
        if (DEBUG) {
            console.info(`[INFO]${this.context ? ` ${this.context}:` : ''}`, ...args);
        }
    }

    /**
     * Warning level - uyarılar (production'da da gösterilir)
     */
    warn(...args) {
        console.warn(`[WARN]${this.context ? ` ${this.context}:` : ''}`, ...args);
    }

    /**
     * Error level - hatalar (her zaman gösterilir)
     */
    error(...args) {
        console.error(`[ERROR]${this.context ? ` ${this.context}:` : ''}`, ...args);

        // Production'da error tracking service'e gönder (örnek: Sentry)
        if (isProduction() && window.Sentry) {
            window.Sentry.captureException(args[0]);
        }
    }

    /**
     * API request logging
     */
    apiRequest(method, endpoint, data = null) {
        if (DEBUG) {
            console.log(
                `%c[API] ${method} ${endpoint}`,
                'color: #4CAF50; font-weight: bold',
                data || ''
            );
        }
    }

    /**
     * API response logging
     */
    apiResponse(endpoint, status, data = null) {
        if (DEBUG) {
            const color = status >= 200 && status < 300 ? '#4CAF50' : '#F44336';
            console.log(
                `%c[API] ${status} ${endpoint}`,
                `color: ${color}; font-weight: bold`,
                data || ''
            );
        }
    }

    /**
     * Performance timing
     */
    time(label) {
        if (DEBUG) {
            console.time(label);
        }
    }

    timeEnd(label) {
        if (DEBUG) {
            console.timeEnd(label);
        }
    }
}

// Default logger instance
export const logger = new Logger();

// Contextual loggers
export const createLogger = (context) => new Logger(context);

// Convenience exports
export default {
    Logger,
    logger,
    createLogger,
    isProduction
};
