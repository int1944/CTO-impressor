# Travel Booking UI

React-based frontend for the Travel Booking Assistant, featuring real-time suggestions, entity highlighting, and interactive widgets.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Make sure the suggestion API is running on `http://localhost:8000`

## Environment Variables

Create a `.env` file:
```
VITE_API_URL=http://localhost:8000
```

## Features

- Real-time suggestion fetching with debouncing
- Entity highlighting in input field
- Interactive suggestion cards
- Calendar widget for date selection
- City list widget for location selection
- Placeholder tags showing missing slots
- Responsive design with Tailwind CSS

## Project Structure

- `src/components/` - React components
- `src/hooks/` - Custom React hooks
- `src/services/` - API service layer
- `src/utils/` - Utility functions
- `src/styles/` - Global styles and Tailwind config
