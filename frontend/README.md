# Interactive Reading Platform - Frontend

A React-based frontend for the Interactive Reading Platform, designed to provide personalized AI-powered storytelling experiences for children aged 7-12.

## Features

- **Child-Friendly UI**: Designed specifically for young readers with large, clear text and engaging visuals
- **Multi-language Support**: Hebrew and English language support with proper RTL/LTR text direction
- **Interactive Storytelling**: Choice-driven narratives that adapt based on user selections
- **Text-to-Speech**: Built-in audio playback for stories with highlighting
- **Progress Tracking**: Save and resume reading progress
- **Responsive Design**: Works seamlessly on desktop and tablet devices

## Tech Stack

- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite for fast development and optimized builds
- **Styling**: Tailwind CSS with custom child-friendly theme
- **State Management**: Zustand for lightweight state management
- **Routing**: React Router v6 for client-side navigation
- **Code Quality**: ESLint, Prettier, and TypeScript for development standards

## Getting Started

### Prerequisites

- Node.js 18+ LTS
- npm or yarn package manager

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development Scripts

```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Run TypeScript type checking
npm run type-check

# Lint code with ESLint
npm run lint
npm run lint:fix

# Format code with Prettier
npm run format
npm run format:check

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── layout/         # Layout components (Header, Layout, etc.)
│   └── ui/            # Basic UI components (Button, Spinner, etc.)
├── pages/              # Route-based page components
│   ├── auth/          # Authentication pages
│   ├── child/         # Child-specific pages
│   └── reading/       # Reading interface pages
├── stores/            # Zustand state management stores
├── types/             # TypeScript type definitions
├── hooks/             # Custom React hooks
├── services/          # API service functions
└── utils/             # Utility functions and helpers
```

## Development Guidelines

### Code Style
- Use TypeScript for all new files
- Follow React functional component patterns
- Use custom hooks for complex logic
- Maintain consistent naming conventions

### Component Structure
- Keep components focused and single-purpose
- Use TypeScript interfaces for props
- Include proper error handling
- Add loading states for async operations

## Multi-language Support

The application supports Hebrew and English with:
- Automatic RTL/LTL text direction
- Language-specific fonts
- Localized user interface text
- Language preference storage

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
