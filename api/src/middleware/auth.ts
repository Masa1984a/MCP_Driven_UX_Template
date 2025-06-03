import { Request, Response, NextFunction } from 'express';
import { logger } from '../utils/logger';

// Extend Express Request type to include API key info
declare module 'express-serve-static-core' {
  interface Request {
    apiKey?: string;
  }
}

/**
 * Middleware to authenticate API requests using API key
 */
export const authenticateAPIKey = (req: Request, res: Response, next: NextFunction) => {
  // Skip authentication for health check endpoint
  if (req.path === '/health') {
    return next();
  }

  // Check if authentication should be disabled (for local development)
  const disableAuth = process.env.DISABLE_AUTH === 'true' || process.env.NODE_ENV === 'development';
  if (disableAuth) {
    logger.info('API key authentication disabled for local development');
    return next();
  }

  const apiKey = req.headers['x-api-key'] as string;
  const expectedApiKey = process.env.API_KEY;

  // If no API key is configured, log warning and allow request (development mode)
  if (!expectedApiKey) {
    logger.warn('API_KEY not configured - API key authentication disabled');
    return next();
  }

  // Check if API key is provided
  if (!apiKey) {
    logger.error('Missing API key in request', { 
      path: req.path, 
      method: req.method,
      ip: req.ip 
    });
    return res.status(401).json({
      error: 'Missing API key',
      message: 'Please provide an API key in the x-api-key header'
    });
  }

  // Validate API key
  if (apiKey !== expectedApiKey) {
    logger.error('Invalid API key provided', { 
      path: req.path, 
      method: req.method,
      ip: req.ip,
      providedKey: apiKey.substring(0, 5) + '...' // Log first 5 chars for debugging
    });
    return res.status(401).json({
      error: 'Invalid API key',
      message: 'The provided API key is not valid'
    });
  }

  // Store API key in request for potential logging
  req.apiKey = apiKey;
  
  logger.info('API request authenticated', {
    path: req.path,
    method: req.method,
    ip: req.ip
  });

  next();
};

/**
 * Optional middleware to log API usage
 */
export const logAPIUsage = (req: Request, res: Response, next: NextFunction) => {
  const startTime = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    logger.info('API request completed', {
      path: req.path,
      method: req.method,
      statusCode: res.statusCode,
      duration: `${duration}ms`,
      apiKey: req.apiKey ? req.apiKey.substring(0, 5) + '...' : 'none'
    });
  });
  
  next();
};