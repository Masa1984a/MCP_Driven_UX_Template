FROM node:20-slim

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Build TypeScript without pgtyped
RUN npm run build:ci

# Expose the API port
EXPOSE 8080

# Start the application
CMD ["node", "build/src/index.js"]