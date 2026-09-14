FROM node:18-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy project
COPY . .

# Expose port (Vite default is 5173)
EXPOSE 5173

# Start command
CMD ["sh", "-c", "rm -rf node_modules/.bin && npm install && npm run dev -- --host"]
