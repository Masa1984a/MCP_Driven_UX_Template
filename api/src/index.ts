import express from 'express';
import { Pool } from 'pg';
import { logger } from './utils/logger';
import { ticketRoutes } from './routes/ticketRoutes';
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config({ path: './.env' });

// Create Express app
const app = express();
app.use(express.json());

// Configure PostgreSQL connection
const pool = new Pool({
  host: process.env.DB_HOST || 'db',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'mcp_ux',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres'
});

// Test database connection
pool.connect()
  .then(client => {
    logger.info('Connected to PostgreSQL database');
    client.release();
  })
  .catch(err => {
    logger.error('Failed to connect to PostgreSQL database', { error: err.message });
  });

// Make pool available in request context
app.use((req, res, next) => {
  req.db = pool;
  next();
});

// Enable CORS
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
  if (req.method === 'OPTIONS') {
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH');
    return res.status(200).json({});
  }
  next();
});

// Register routes
app.use('/tickets', ticketRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Error handling
app.use((err: Error, req: express.Request, res: express.Response, _next: express.NextFunction) => {
  logger.error('Unhandled error', { error: err.message, stack: err.stack });
  res.status(500).json({
    error: {
      message: 'An unexpected error occurred',
    }
  });
});

// Start the server
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  logger.info(`Server is running on port ${PORT}`);
});