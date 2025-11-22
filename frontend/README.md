# AI-Researcher Frontend

Vue.js 3 frontend application for the AI-Researcher backend.

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Vue components
│   ├── composables/     # Composition API composables
│   ├── stores/          # Pinia stores
│   ├── services/        # API services
│   ├── views/           # Route views
│   ├── router/          # Vue Router config
│   ├── types/           # TypeScript types
│   └── utils/           # Utility functions
├── public/              # Static assets
└── tests/               # Test files
```

## Getting Started

### Prerequisites

- Node.js 18+ or 20+
- pnpm (recommended) or npm/yarn

### Installation

```bash
# Install dependencies
pnpm install

# Copy environment file
cp .env.example .env

# Edit .env and set your API base URL
# VITE_API_BASE_URL=http://localhost:8080
```

### Development

```bash
# Start development server
pnpm dev

# Run linter
pnpm lint

# Run type checking
pnpm type-check

# Run tests
pnpm test
```

### Build

```bash
# Build for production
pnpm build

# Preview production build
pnpm preview
```

## Key Features

- ✅ Vue.js 3 with Composition API
- ✅ TypeScript support
- ✅ Pinia state management
- ✅ Vue Router for routing
- ✅ Axios for API calls
- ✅ Polling-based log streaming
- ✅ Session persistence
- ✅ Error handling
- ✅ Responsive design

## Components to Implement

### Core Components
- [x] AppHeader
- [x] AppFooter
- [ ] QueryInput
- [ ] ModeSelector
- [ ] ConversationInterface
- [ ] LogViewer
- [ ] ProgressTracker
- [ ] ResultVisualization
- [ ] PaperViewer

### Views
- [x] Home
- [x] NotFound
- [ ] Jobs
- [ ] JobDetail
- [ ] Environment
- [ ] Settings

## Environment Variables

See `.env.example` for required environment variables.

## API Integration

The frontend uses the API client defined in `src/services/api/`. All API calls are type-safe using TypeScript interfaces defined in `src/types/api.ts`.

## State Management

State is managed using Pinia stores:
- `job` - Job management
- `environment` - Environment variables
- `session` - UI state and persistence
- `logs` - Log state

## Polling Strategy

The app uses polling with exponential backoff for:
- Job status updates
- Log streaming
- Progress tracking

Default polling interval: 2 seconds (configurable via env vars)

## Testing

Tests are written using Vitest and Vue Test Utils:

```bash
# Run all tests
pnpm test

# Run tests in watch mode
pnpm test:ui

# Run tests with coverage
pnpm test:coverage
```

## Code Quality

- ESLint for linting
- Prettier for formatting
- TypeScript for type safety
- Husky for git hooks

## Deployment

Build the application:

```bash
pnpm build
```

The `dist/` directory contains the production build ready to be deployed to any static hosting service.

## License

See parent repository for license information.

