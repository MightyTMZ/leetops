# LeetOps Frontend

This is the frontend application for LeetOps - the standardized benchmark for on-call engineering reliability.

## Features

- **Authentication System**: Login/logout with JWT tokens
- **Company Selection**: Browse and select from 40+ tech companies
- **Real-time Simulation**: Handle realistic incident response scenarios
- **Rating Dashboard**: Track your engineering credibility score
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **React Hook Form** - Form handling with validation
- **Axios** - HTTP client for API communication
- **Lucide React** - Beautiful icons
- **Zod** - Schema validation

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Copy environment configuration:
```bash
cp .env.local.example .env.local
```

3. Update the API URL in `.env.local` to point to your backend:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
app/
├── dashboard/          # Company selection page
├── login/             # Authentication page
├── rating/            # User rating dashboard
├── simulation/        # Incident resolution interface
│   └── [companyId]/   # Dynamic company simulation
├── layout.tsx         # Root layout with auth provider
└── page.tsx          # Landing page

lib/
├── api.ts            # API client and endpoints
├── auth.tsx          # Authentication context
└── utils.ts          # Utility functions
```

## API Integration

The frontend integrates with the Django backend through RESTful APIs:

- **Authentication**: JWT token-based auth
- **Companies**: Fetch company data and details
- **Simulations**: Start, manage, and end simulation sessions
- **Incidents**: Generate and resolve incidents
- **Ratings**: Track user performance and ratings

## Key Components

### Authentication
- JWT token management with automatic refresh
- Protected routes and redirects
- User context throughout the app

### Company Selection
- Grid layout with company cards
- Detailed company information
- Tech stack and statistics display

### Simulation Interface
- Real-time incident display
- Timer countdown for urgency
- Resolution form with multiple fields
- Command execution tracking

### Rating Dashboard
- Overall rating display
- Skill breakdown with progress bars
- Performance statistics
- Recent performance trends

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API base URL
- `NEXT_PUBLIC_DEBUG` - Enable debug mode

## Deployment

The frontend is built as a static Next.js application and can be deployed to:

- Vercel (recommended)
- Netlify
- AWS S3 + CloudFront
- Any static hosting service

Make sure to set the `NEXT_PUBLIC_API_URL` environment variable to your production backend URL.