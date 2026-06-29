import { Outlet, Link, useLocation } from 'react-router-dom';
import { Factory, Clock, Github } from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { label: '首页', href: '/', icon: Factory },
  { label: '历史', href: '/history', icon: Clock },
];

export function MainLayout() {
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 font-semibold text-lg">
              <Factory className="w-6 h-6 text-primary-600" />
              <span>AI Project Factory</span>
            </Link>

            {/* Navigation */}
            <nav className="flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    className={cn(
                      'flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-muted hover:text-foreground hover:bg-gray-100',
                    )}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                );
              })}

              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium text-muted hover:text-foreground hover:bg-gray-100 transition-colors ml-2"
              >
                <Github className="w-4 h-4" />
                GitHub
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t py-4 text-center text-sm text-muted">
        <div className="max-w-7xl mx-auto px-4">
          © 2025 AI Project Factory · Powered by Claude
        </div>
      </footer>
    </div>
  );
}
