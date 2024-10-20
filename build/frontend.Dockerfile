# Use a specific version of Node.js
FROM node:23

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and install dependencies
COPY ../src/frontend/package.json .
RUN npm install

# Copy the rest of the frontend application code
COPY ../src/frontend/. .

# Command to start the React application
CMD ["npm", "start"]