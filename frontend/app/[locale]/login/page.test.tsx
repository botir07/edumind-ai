import { render, screen } from "@testing-library/react";
import React from "react";
import { vi } from "vitest";

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => String(key),
  usePathname: () => "/",
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/",
}));

vi.mock("next/link", () => ({
  default: ({ children, ...props }: any) => (
    <a {...props}>{children}</a>
  ),
}));

vi.mock("@/lib/auth", () => ({
  useSession: () => ({
    session: {
      loaded: true,
      user: { full_name: "Test", email: "t@e.uz" },
      memberships: [],
    },
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
  }),
  SessionProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

import LoginPage from "@/app/[locale]/login/page";

describe("Login page", () => {
  it("renders login form fields", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /login/i })).toBeInTheDocument();
  });
});
