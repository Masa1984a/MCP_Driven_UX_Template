import winston from 'winston';
import { logger } from '../../../utils/logger';

describe('Logger', () => {
  it('should be an instance of winston logger', () => {
    expect(logger).toBeDefined();
    expect(logger).toHaveProperty('info');
    expect(logger).toHaveProperty('error');
    expect(logger).toHaveProperty('warn');
    expect(logger).toHaveProperty('debug');
  });

  it('should have correct log level based on environment', () => {
    const expectedLevel = process.env.LOG_LEVEL || 'info';
    expect(logger.level).toBe(expectedLevel);
  });

  it('should log messages without errors', () => {
    expect(() => {
      logger.info('Test info message');
      logger.error('Test error message');
      logger.warn('Test warning message');
      logger.debug('Test debug message');
    }).not.toThrow();
  });
});