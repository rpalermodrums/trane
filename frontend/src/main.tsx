import { StrictMode } from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  Outlet,
  RouterProvider,
  createRouter,
  createRoute,
  createRootRoute,
} from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'
import { ProtectedRoute } from './components/ProtectedRoute'
import Login from './components/Login'
import Home from './pages/Home'
import './index.css'
import { PlaybackView } from './pages/PlaybackView'
import { Settings } from './pages/Settings'
import { Navigation } from './components/Navigation'

const rootRoute = createRootRoute({
  component: () => {
    return (
      <div className="w-screen h-screen">
        <Navigation />
        <hr />
        <Outlet />
        <TanStackRouterDevtools />
      </div>
    )
  },
})

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: Login,
});

const protectedRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: 'protected',
  component: ProtectedRoute,
});

const indexRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: '/',
  component: Home,
});

const playbackRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: '/playback/$entryId',
  component: PlaybackView,
});

const settingsRoute = createRoute({
  getParentRoute: () => protectedRoute,
  path: '/settings',
  component: Settings,
});

const routeTree = rootRoute.addChildren([
  loginRoute,
  protectedRoute.addChildren([
    indexRoute,
    settingsRoute,
    playbackRoute,
  ]),
])

const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

const queryClient = new QueryClient();

// biome-ignore lint/style/noNonNullAssertion: <ReactDOM Root Element, see index.html>
const rootElement = document.getElementById('root')!
if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement)
  root.render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </StrictMode>,
  )
}