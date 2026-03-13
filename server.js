const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB Connection
mongoose.connect('mongodb://localhost:27017/techsphere', { useNewUrlParser: true, useUnifiedTopology: true })
  .then(() => console.log('MongoDB connected'))
  .catch(err => console.error('MongoDB connection error:', err));

// API Routes
app.use('/api/news', require('./routes/news'));  // news routes
app.use('/api/events', require('./routes/events'));  // events routes
app.use('/api/competitions', require('./routes/competitions'));  // competitions routes
app.use('/api/auth', require('./routes/auth'));  // auth routes
app.use('/api/users', require('./routes/users'));  // user routes

// Start Server
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
