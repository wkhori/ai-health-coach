"use client";

import { useState, useCallback, type FormEvent } from "react";
import { useAuth } from "@/components/auth/auth-provider";
import { authLogin, authRegister } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Heart } from "lucide-react";

export function LoginForm() {
  const { setUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const doLogin = useCallback(
    async (loginEmail: string, loginPassword: string) => {
      setError(null);
      setLoading(true);
      try {
        const { user } = await authLogin(loginEmail, loginPassword);
        setUser(user);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Authentication failed"
        );
      } finally {
        setLoading(false);
      }
    },
    [setUser]
  );

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      setError(null);
      setLoading(true);

      try {
        if (isSignUp) {
          const { user } = await authRegister(email, password, name);
          setUser(user);
        } else {
          const { user } = await authLogin(email, password);
          setUser(user);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Authentication failed"
        );
      } finally {
        setLoading(false);
      }
    },
    [email, password, name, isSignUp, setUser]
  );

  return (
    <div className="flex min-h-full items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-900">
            <Heart className="size-6 text-emerald-600 dark:text-emerald-400" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight">
            Stride
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {isSignUp
              ? "Create an account to get started"
              : "Sign in to continue your wellness journey"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300">
              {error}
            </div>
          )}

          {isSignUp && (
            <div className="space-y-2">
              <label
                htmlFor="name"
                className="text-sm font-medium text-foreground"
              >
                Name
              </label>
              <Input
                id="name"
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
              />
            </div>
          )}

          <div className="space-y-2">
            <label
              htmlFor="email"
              className="text-sm font-medium text-foreground"
            >
              Email
            </label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="space-y-2">
            <label
              htmlFor="password"
              className="text-sm font-medium text-foreground"
            >
              Password
            </label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete={isSignUp ? "new-password" : "current-password"}
              minLength={6}
            />
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-emerald-600 text-white hover:bg-emerald-700 dark:bg-emerald-700 dark:hover:bg-emerald-600"
          >
            {loading
              ? "Please wait..."
              : isSignUp
                ? "Create account"
                : "Sign in"}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
          <button
            type="button"
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError(null);
            }}
            className="font-medium text-emerald-600 hover:underline dark:text-emerald-400"
          >
            {isSignUp ? "Sign in" : "Sign up"}
          </button>
        </p>

        <div className="rounded-lg border border-dashed border-muted-foreground/30 p-3 text-xs text-muted-foreground">
          <p className="mb-2 text-center font-medium">Quick login as demo patient</p>
          <div className="space-y-1.5">
            {[
              { email: "sarah@demo.com", name: "Sarah", phase: "Active" },
              { email: "marcus@demo.com", name: "Marcus", phase: "Onboarding" },
              { email: "elena@demo.com", name: "Elena", phase: "Re-engaging" },
            ].map((demo) => (
              <button
                key={demo.email}
                type="button"
                disabled={loading}
                onClick={() => doLogin(demo.email, "password123")}
                className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-left transition-colors hover:bg-muted disabled:opacity-50"
              >
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300">
                  {demo.name[0]}
                </span>
                <span className="flex-1">
                  <span className="font-medium text-foreground">{demo.name}</span>
                  <span className="ml-1.5 text-muted-foreground/60">{demo.phase}</span>
                </span>
                <span className="text-[10px] text-muted-foreground/40">{demo.email}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
