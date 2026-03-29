"use client";

import { useState, useCallback, useEffect } from "react";
import { useAuth } from "@/components/auth/auth-provider";
import { LoginForm } from "@/components/auth/login-form";
import { PatientSwitcher } from "@/components/patient-switcher";
import { PatientSidebar } from "@/components/sidebar/patient-sidebar";
import { ChatContainer } from "@/components/chat/chat-container";
import { ConsentBanner } from "@/components/consent-banner";
import { DemoControls } from "@/components/demo-controls";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { patients, DEMO_MODE } from "@/lib/demo-data";
import {
  fetchProfile,
  fetchGoals,
  fetchConversation,
  grantConsent,
  resetDemo,
  apiGoalToGoal,
  apiTurnToMessage,
  computeAdherence,
  type ApiProfile,
} from "@/lib/api";
import type { Goal, Message, AdherenceStats, Phase, SafetyResult, ToolCall } from "@/lib/types";
import Link from "next/link";
import { PanelLeft, Heart, LogOut, Loader2, LayoutDashboard } from "lucide-react";

export default function Home() {
  // ── Demo mode state ────────────────────────────────────────────
  const [currentPatientId, setCurrentPatientId] = useState("sarah");
  const [consentOverrides, setConsentOverrides] = useState<
    Record<string, boolean>
  >({});
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // ── Real mode state ────────────────────────────────────────────
  const { user, loading: authLoading, signOut } = useAuth();
  const [profile, setProfile] = useState<ApiProfile | null>(null);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [adherence, setAdherence] = useState<AdherenceStats>({
    streak: 0,
    weeklyCompletion: 0,
    trend: "stable",
  });
  const [conversation, setConversation] = useState<Message[]>([]);
  const [dataLoading, setDataLoading] = useState(false);
  const [dataError, setDataError] = useState<string | null>(null);

  // ── Demo controls state ────────────────────────────────────────
  const [safetyResult, setSafetyResult] = useState<SafetyResult | null>(null);
  const [recentToolCalls, setRecentToolCalls] = useState<ToolCall[]>([]);

  // ── Load real data when authenticated ──────────────────────────
  const loadData = useCallback(async () => {
    if (DEMO_MODE || !user) return;
    setDataLoading(true);
    setDataError(null);
    try {
      const [profileRes, goalsRes, convoRes] = await Promise.all([
        fetchProfile(),
        fetchGoals(),
        fetchConversation(),
      ]);
      setProfile(profileRes);
      const mappedGoals = goalsRes.map(apiGoalToGoal);
      setGoals(mappedGoals);
      setAdherence(computeAdherence(mappedGoals));
      setConversation(convoRes.turns.map(apiTurnToMessage));
    } catch (err) {
      setDataError(
        err instanceof Error ? err.message : "Failed to load data"
      );
    } finally {
      setDataLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ── Refetch goals (called after chat events) ───────────────────
  const refetchGoals = useCallback(async () => {
    if (DEMO_MODE || !user) return;
    try {
      const goalsRes = await fetchGoals();
      const mappedGoals = goalsRes.map(apiGoalToGoal);
      setGoals(mappedGoals);
      setAdherence(computeAdherence(mappedGoals));
    } catch {
      // Silent fail on background refetch
    }
  }, [user]);

  // ── Refetch profile (called after consent/phase change) ────────
  const refetchProfile = useCallback(async () => {
    if (DEMO_MODE || !user) return;
    try {
      const profileRes = await fetchProfile();
      setProfile(profileRes);
    } catch {
      // Silent fail on background refetch
    }
  }, [user]);

  // ── Consent handler ────────────────────────────────────────────
  const handleConsent = useCallback(async () => {
    if (DEMO_MODE) {
      setConsentOverrides((prev) => ({
        ...prev,
        [currentPatientId]: true,
      }));
      return;
    }
    try {
      await grantConsent("1.0");
      await refetchProfile();
    } catch (err) {
      setDataError(
        err instanceof Error ? err.message : "Failed to grant consent"
      );
    }
  }, [currentPatientId, refetchProfile]);

  // ── Auth loading state ─────────────────────────────────────────
  if (!DEMO_MODE && authLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // ── Not authenticated (real mode) ──────────────────────────────
  if (!DEMO_MODE && !user) {
    return <LoginForm />;
  }

  // ── Data loading state (real mode) ─────────────────────────────
  if (!DEMO_MODE && dataLoading && !profile) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
        <p className="text-sm text-muted-foreground">Loading your profile...</p>
      </div>
    );
  }

  // ── Data error state (real mode) ───────────────────────────────
  if (!DEMO_MODE && dataError && !profile) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3">
        <p className="text-sm text-red-600 dark:text-red-400">{dataError}</p>
        <Button onClick={loadData} variant="outline" size="sm">
          Retry
        </Button>
      </div>
    );
  }

  // ── Determine data source ──────────────────────────────────────
  let displayName: string;
  let displayPhase: Phase;
  let displayGoals: Goal[];
  let displayAdherence: AdherenceStats;
  let displayConversation: Message[];
  let hasConsent: boolean;

  if (DEMO_MODE) {
    const patient = patients[currentPatientId];
    displayName = patient.name;
    displayPhase = patient.phase;
    displayGoals = patient.goals;
    displayAdherence = patient.adherence;
    displayConversation = patient.conversation;
    hasConsent = consentOverrides[currentPatientId] ?? patient.consentGiven;
  } else {
    displayName = profile?.name ?? user?.email ?? "User";
    displayPhase = profile?.phase ?? "PENDING";
    displayGoals = goals;
    displayAdherence = adherence;
    displayConversation = conversation;
    hasConsent = profile?.consent_given_at != null;
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <header className="flex h-13 shrink-0 items-center justify-between border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="flex items-center gap-3">
          {/* Mobile sidebar trigger */}
          <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
            <SheetTrigger
              render={
                <Button variant="ghost" size="icon-sm" className="lg:hidden" />
              }
            >
              <PanelLeft className="size-4" />
              <span className="sr-only">Toggle sidebar</span>
            </SheetTrigger>
            <SheetContent side="left" className="w-72 p-0">
              <SheetTitle className="sr-only">Patient sidebar</SheetTitle>
              <SheetDescription className="sr-only">
                View patient details, goals and stats
              </SheetDescription>
              <PatientSidebar
                name={displayName}
                phase={displayPhase}
                goals={displayGoals}
                adherence={displayAdherence}
              />
            </SheetContent>
          </Sheet>

          <div className="flex items-center gap-2">
            <div className="flex size-7 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900">
              <Heart className="size-3.5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <h1 className="text-sm font-semibold tracking-tight">
              Health Coach
            </h1>
          </div>

          {DEMO_MODE && (
            <Badge
              variant="outline"
              className="hidden text-[10px] font-normal text-muted-foreground sm:inline-flex"
            >
              Demo Mode
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Link href="/dashboard" aria-label="Clinician Dashboard">
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-muted-foreground"
              title="Clinician Dashboard"
              aria-label="Clinician Dashboard"
            >
              <LayoutDashboard className="size-4" />
            </Button>
          </Link>
          {DEMO_MODE ? (
            <PatientSwitcher
              currentPatientId={currentPatientId}
              onSwitch={setCurrentPatientId}
            />
          ) : (
            <Button
              variant="ghost"
              size="sm"
              onClick={signOut}
              className="gap-1.5 text-muted-foreground"
            >
              <LogOut className="size-3.5" />
              <span className="hidden sm:inline">Sign out</span>
            </Button>
          )}
        </div>
      </header>

      {/* Consent banner */}
      {!hasConsent && <ConsentBanner onConsent={handleConsent} />}

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Desktop sidebar */}
        <aside className="hidden w-72 shrink-0 border-r bg-sidebar lg:block">
          <PatientSidebar
            name={displayName}
            phase={displayPhase}
            goals={displayGoals}
            adherence={displayAdherence}
          />
        </aside>

        {/* Chat area */}
        <main className="flex-1 overflow-hidden">
          <ChatContainer
            patientId={DEMO_MODE ? currentPatientId : (profile?.id ?? "")}
            initialMessages={displayConversation}
            disabled={!hasConsent}
            demoMode={DEMO_MODE}
            phase={displayPhase}
            onGoalsChanged={refetchGoals}
            onPhaseChanged={refetchProfile}
            onSafetyResult={setSafetyResult}
            onToolCall={(tc) =>
              setRecentToolCalls((prev) => [...prev.slice(-9), tc])
            }
          />
        </main>
      </div>

      {/* Demo controls panel */}
      <DemoControls
        phase={displayPhase}
        safetyResult={safetyResult}
        toolCalls={recentToolCalls}
        demoMode={DEMO_MODE}
        onReset={async () => {
          if (!DEMO_MODE) {
            try {
              await resetDemo();
            } catch {
              // Ignore reset errors
            }
          }
          window.location.reload();
        }}
      />
    </div>
  );
}
