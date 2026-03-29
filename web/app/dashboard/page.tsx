"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@/components/auth/auth-provider";
import { LoginForm } from "@/components/auth/login-form";
import { PhaseBadge } from "@/components/sidebar/phase-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { DEMO_MODE, dashboardPatients, dashboardAlerts } from "@/lib/demo-data";
import { fetchAdminPatients, fetchAdminAlerts } from "@/lib/api";
import type { DashboardPatient, DashboardAlert, Phase } from "@/lib/types";
import {
  ArrowLeft,
  Heart,
  Users,
  AlertTriangle,
  Target,
  TrendingUp,
  Clock,
  Loader2,
  ShieldAlert,
} from "lucide-react";

const PHASE_CONFIG: Record<
  Phase,
  { label: string; color: string; bg: string }
> = {
  PENDING: {
    label: "Pending",
    color: "text-zinc-600 dark:text-zinc-400",
    bg: "bg-zinc-100 dark:bg-zinc-800",
  },
  ONBOARDING: {
    label: "Onboarding",
    color: "text-blue-600 dark:text-blue-400",
    bg: "bg-blue-50 dark:bg-blue-950/30",
  },
  ACTIVE: {
    label: "Active",
    color: "text-emerald-600 dark:text-emerald-400",
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
  },
  RE_ENGAGING: {
    label: "Re-engaging",
    color: "text-amber-600 dark:text-amber-400",
    bg: "bg-amber-50 dark:bg-amber-950/30",
  },
  DORMANT: {
    label: "Dormant",
    color: "text-red-600 dark:text-red-400",
    bg: "bg-red-50 dark:bg-red-950/30",
  },
};

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "Never";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function Dashboard() {
  const { user, loading: authLoading } = useAuth();
  const [patients, setPatients] = useState<DashboardPatient[]>([]);
  const [alerts, setAlerts] = useState<DashboardAlert[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (DEMO_MODE) {
      setPatients(dashboardPatients);
      setAlerts(dashboardAlerts);
      setLoading(false);
      return;
    }
    try {
      const [p, a] = await Promise.all([
        fetchAdminPatients(),
        fetchAdminAlerts(),
      ]);
      setPatients(p);
      setAlerts(a);
    } catch {
      // Fallback to demo data on error
      setPatients(dashboardPatients);
      setAlerts(dashboardAlerts);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auth gate for real mode
  if (!DEMO_MODE && authLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }
  if (!DEMO_MODE && !user) {
    return <LoginForm />;
  }

  // Phase distribution
  const phaseCounts = patients.reduce(
    (acc, p) => {
      acc[p.phase] = (acc[p.phase] || 0) + 1;
      return acc;
    },
    {} as Record<Phase, number>
  );

  const totalPatients = patients.length;

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <header className="flex h-13 shrink-0 items-center justify-between border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="flex items-center gap-3">
          <div className="flex size-7 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900">
            <Heart className="size-3.5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <h1 className="text-sm font-semibold tracking-tight">
            Clinician Dashboard
          </h1>
          {DEMO_MODE && (
            <Badge
              variant="outline"
              className="hidden text-[10px] font-normal text-muted-foreground sm:inline-flex"
            >
              Demo Mode
            </Badge>
          )}
        </div>
        <Link href="/">
          <Button variant="ghost" size="sm" className="gap-1.5 text-muted-foreground">
            <ArrowLeft className="size-3.5" />
            <span className="hidden sm:inline">Back to Chat</span>
          </Button>
        </Link>
      </header>

      {/* Content */}
      <ScrollArea className="flex-1">
        <div className="mx-auto max-w-5xl space-y-6 p-4 sm:p-6">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              {/* Phase Distribution */}
              <section>
                <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
                  <Users className="size-4 text-muted-foreground" />
                  Patient Overview
                  <Badge variant="secondary" className="ml-1 text-xs">
                    {totalPatients}
                  </Badge>
                </h2>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
                  {(
                    [
                      "PENDING",
                      "ONBOARDING",
                      "ACTIVE",
                      "RE_ENGAGING",
                      "DORMANT",
                    ] as Phase[]
                  ).map((phase) => {
                    const config = PHASE_CONFIG[phase];
                    const count = phaseCounts[phase] || 0;
                    return (
                      <Card key={phase} className={config.bg}>
                        <CardContent className="p-3">
                          <p
                            className={`text-[10px] font-semibold uppercase tracking-wider ${config.color}`}
                          >
                            {config.label}
                          </p>
                          <p className="mt-1 text-2xl font-bold">{count}</p>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </section>

              {/* Safety Alerts */}
              {alerts.length > 0 && (
                <section>
                  <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
                    <ShieldAlert className="size-4 text-amber-500" />
                    Active Alerts
                    <Badge variant="destructive" className="ml-1 text-xs">
                      {alerts.length}
                    </Badge>
                  </h2>
                  <div className="space-y-2">
                    {alerts.map((alert) => (
                      <Card
                        key={alert.id}
                        className={
                          alert.urgency === "urgent"
                            ? "border-red-300 dark:border-red-800"
                            : "border-amber-200 dark:border-amber-800"
                        }
                      >
                        <CardContent className="flex items-start gap-3 p-3">
                          <AlertTriangle
                            className={`mt-0.5 size-4 shrink-0 ${
                              alert.urgency === "urgent"
                                ? "text-red-500"
                                : "text-amber-500"
                            }`}
                          />
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium">
                                {alert.patient_name}
                              </span>
                              <Badge
                                variant={
                                  alert.urgency === "urgent"
                                    ? "destructive"
                                    : "outline"
                                }
                                className="text-[10px]"
                              >
                                {alert.urgency}
                              </Badge>
                              <span className="text-[10px] text-muted-foreground">
                                {alert.alert_type}
                              </span>
                            </div>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {alert.message}
                            </p>
                          </div>
                          <span className="shrink-0 text-[10px] text-muted-foreground">
                            {timeAgo(alert.created_at)}
                          </span>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </section>
              )}

              {/* Patient Table */}
              <section>
                <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
                  <Target className="size-4 text-muted-foreground" />
                  All Patients
                </h2>
                <Card>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b text-left text-xs text-muted-foreground">
                          <th className="px-4 py-2.5 font-medium">Patient</th>
                          <th className="px-4 py-2.5 font-medium">Phase</th>
                          <th className="hidden px-4 py-2.5 font-medium sm:table-cell">
                            Last Activity
                          </th>
                          <th className="px-4 py-2.5 font-medium text-center">
                            Goals
                          </th>
                          <th className="px-4 py-2.5 font-medium text-center">
                            Adherence
                          </th>
                          <th className="hidden px-4 py-2.5 font-medium text-center sm:table-cell">
                            Alerts
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {patients.map((patient) => (
                          <tr
                            key={patient.user_id}
                            className="border-b last:border-0 transition-colors hover:bg-muted/30"
                          >
                            <td className="px-4 py-3 font-medium">
                              {patient.display_name}
                            </td>
                            <td className="px-4 py-3">
                              <PhaseBadge phase={patient.phase} />
                            </td>
                            <td className="hidden px-4 py-3 sm:table-cell">
                              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Clock className="size-3" />
                                {timeAgo(patient.last_message_at)}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span className="text-xs font-medium">
                                {patient.active_goals_count}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-center">
                              <div className="flex items-center justify-center gap-1">
                                <TrendingUp
                                  className={`size-3 ${
                                    patient.adherence_pct >= 70
                                      ? "text-emerald-500"
                                      : patient.adherence_pct >= 40
                                        ? "text-amber-500"
                                        : "text-red-400"
                                  }`}
                                />
                                <span className="text-xs font-medium">
                                  {patient.adherence_pct}%
                                </span>
                              </div>
                            </td>
                            <td className="hidden px-4 py-3 text-center sm:table-cell">
                              {patient.alerts_count > 0 ? (
                                <Badge
                                  variant="destructive"
                                  className="text-[10px]"
                                >
                                  {patient.alerts_count}
                                </Badge>
                              ) : (
                                <span className="text-xs text-muted-foreground">
                                  0
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              </section>
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
