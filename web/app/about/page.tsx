"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AppPreviewPlayer } from "@/components/app-preview-player";
import {
  Heart,
  ArrowLeft,
  Brain,
  Shield,
  GitBranch,
  AlertTriangle,
  Workflow,
  Lock,
  BarChart3,
  Bot,
  MessageSquare,
  Wrench,
  TestTube,
  Monitor,
  Zap,
  Database,
  Activity,
} from "lucide-react";

// ── Animation variants ──────────────────────────────────────────────
const fadeInUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
};

const stagger = {
  visible: {
    transition: { staggerChildren: 0.08 },
  },
};

// ── Data ─────────────────────────────────────────────────────────────
const DESIGN_DECISIONS = [
  {
    title: "Two-Tier Safety Classifier",
    decision: "Rules + LLM over LLM-only",
    rationale:
      "Tier 1 regex catches obvious cases in <1ms — fast-pass for safe content, fast-block for crisis keywords. Tier 2 LLM handles ambiguity. This cuts classifier LLM calls by ~70% while keeping false-negative rate under 1%.",
    icon: Shield,
    color: "bg-red-100 dark:bg-red-950 text-red-600 dark:text-red-400",
  },
  {
    title: "Deterministic Phase Routing",
    decision: "Application code over LLM-decided routing",
    rationale:
      "The 5-phase state machine (PENDING → ONBOARDING → ACTIVE → RE_ENGAGING → DORMANT) is pure application code. Phase transitions are never LLM-decided — healthcare requires predictable patient journeys, not probabilistic routing.",
    icon: GitBranch,
    color:
      "bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400",
  },
  {
    title: "Phase-Bound Tool Access",
    decision: "Per-phase tool binding over global access",
    rationale:
      "The LLM gets different tools depending on the patient's phase. Onboarding patients can only set goals. Active patients get adherence tracking and clinician alerts. This prevents the model from calling tools that don't match the patient's stage.",
    icon: Bot,
    color:
      "bg-violet-100 dark:bg-violet-950 text-violet-600 dark:text-violet-400",
  },
  {
    title: "Hard-Coded Crisis Responses",
    decision: "Static verified strings over LLM-generated",
    rationale:
      "Crisis responses include specific hotline numbers (988 Lifeline, Crisis Text Line). LLM hallucination risk is unacceptable for these — they're verified, static strings that bypass the model entirely and auto-alert the care team.",
    icon: AlertTriangle,
    color:
      "bg-orange-100 dark:bg-orange-950 text-orange-600 dark:text-orange-400",
  },
  {
    title: "Consent-Gated Interactions",
    decision: "Verify every request over session-cached consent",
    rationale:
      "Every interaction checks consent before any coaching occurs — not cached, not assumed. The consent gate is a graph node that runs before any subgraph is invoked, so no coaching leaks through on any code path.",
    icon: Lock,
    color:
      "bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400",
  },
];

// ── Component ────────────────────────────────────────────────────────
export default function AboutPage() {
  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <header className="flex h-13 shrink-0 items-center justify-between border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="flex size-7 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900">
              <Heart className="size-3.5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <h1 className="text-sm font-semibold tracking-tight">
              How It Works
            </h1>
          </div>
        </div>
        <Link href="/">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-muted-foreground"
          >
            <ArrowLeft className="size-3.5" />
            Back to App
          </Button>
        </Link>
      </header>

      <ScrollArea className="flex-1 overflow-auto">
        <div className="mx-auto max-w-5xl space-y-16 px-4 py-10 sm:px-6">
          {/* ── Hero ──────────────────────────────────── */}
          <motion.section
            className="text-center"
            initial="hidden"
            animate="visible"
            variants={stagger}
          >
            <motion.div variants={fadeInUp}>
              <div className="mx-auto mb-6 flex size-20 items-center justify-center rounded-2xl bg-emerald-100 dark:bg-emerald-900">
                <Heart className="size-10 text-emerald-600 dark:text-emerald-400" />
              </div>
            </motion.div>
            <motion.h1
              variants={fadeInUp}
              className="text-3xl font-bold tracking-tight sm:text-4xl"
            >
              AI Health Coach
            </motion.h1>
            <motion.p
              variants={fadeInUp}
              className="mx-auto mt-3 max-w-2xl text-lg text-muted-foreground"
            >
              A safety-first AI coaching platform built with a 17-node
              LangGraph agent, two-tier safety classification, and 701 tests
              including 113 adversarial prompts.
            </motion.p>
            <motion.div
              variants={fadeInUp}
              className="mt-6 flex items-center justify-center gap-3"
            >
              <Link href="/">
                <Button className="gap-2 bg-emerald-600 text-white hover:bg-emerald-700">
                  <MessageSquare className="size-4" />
                  Try the App
                </Button>
              </Link>
              <Link href="/dashboard">
                <Button variant="outline" className="gap-2">
                  <BarChart3 className="size-4" />
                  Clinician Dashboard
                </Button>
              </Link>
            </motion.div>
          </motion.section>

          {/* ── Feature Preview ────────────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.div variants={fadeInUp}>
              <AppPreviewPlayer />
            </motion.div>
          </motion.section>

          {/* ── Problem & Approach ────────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.h2
              variants={fadeInUp}
              className="text-2xl font-bold tracking-tight"
            >
              Problem & Approach
            </motion.h2>
            <motion.div
              variants={fadeInUp}
              className="mt-4 space-y-4 text-muted-foreground"
            >
              <p>
                Patients prescribed home exercise programs frequently fall off
                their routines between clinic visits.{" "}
                <strong className="text-foreground">
                  Clinicians don&apos;t have bandwidth for regular motivational
                  check-ins
                </strong>{" "}
                with every patient.
              </p>
              <p>
                I built an AI coaching agent that fills this gap — onboarding
                patients into exercise goals, tracking adherence, and
                proactively re-engaging when they go quiet. The core constraint:{" "}
                <strong className="text-foreground">
                  stay within general wellness boundaries and never cross into
                  clinical advice
                </strong>
                . Every outbound message passes through a safety classifier
                before reaching the patient, and crisis signals trigger
                hard-coded responses with verified hotline numbers.
              </p>
            </motion.div>
          </motion.section>

          {/* ── System Architecture ──────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.div variants={fadeInUp}>
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-emerald-600 dark:text-emerald-400">
                Architecture
              </p>
            </motion.div>
            <motion.h2
              variants={fadeInUp}
              className="mt-1.5 text-2xl font-bold tracking-tight"
            >
              System Design
            </motion.h2>
            <motion.p
              variants={fadeInUp}
              className="mt-2 text-sm text-muted-foreground"
            >
              Three-tier architecture: Next.js frontend connected via SSE to a
              FastAPI server, powered by a LangGraph agent pipeline with
              two-tier safety classification.
            </motion.p>
            <motion.div variants={fadeInUp} className="mt-8">
              <Card className="p-6 sm:p-10">
                {/* ── Client tier ── */}
                <div className="flex justify-center">
                  <div className="inline-flex items-center gap-2.5 rounded-xl border bg-card px-5 py-2.5 shadow-sm">
                    <Monitor className="size-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">Web</p>
                      <p className="text-[11px] text-muted-foreground/70">
                        Next.js
                      </p>
                    </div>
                  </div>
                </div>

                {/* ── Connector ── */}
                <div className="flex flex-col items-center py-1">
                  <div className="h-5 w-px bg-border" />
                  <span className="my-1 text-[11px] text-muted-foreground/60">
                    SSE Streaming
                  </span>
                  <div className="h-5 w-px bg-border" />
                </div>

                {/* ── API tier ── */}
                <div className="flex justify-center">
                  <div className="inline-flex items-center gap-2.5 rounded-xl border bg-card px-5 py-2.5 shadow-sm">
                    <Zap className="size-4 text-amber-500" />
                    <div>
                      <p className="text-sm font-medium">FastAPI</p>
                      <p className="text-[11px] text-muted-foreground/70">
                        API Server
                      </p>
                    </div>
                  </div>
                </div>

                {/* ── Connector ── */}
                <div className="flex justify-center py-1">
                  <div className="h-6 w-px bg-border" />
                </div>

                {/* ── LangGraph Pipeline ── */}
                <div className="rounded-xl border bg-muted/40 p-5 sm:p-6">
                  <p className="text-center text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                    LangGraph Agent Pipeline
                  </p>

                  {/* Top flow: consent → router */}
                  <div className="mt-5 flex items-center justify-center gap-2">
                    <span className="rounded-lg border bg-card px-3 py-1.5 font-mono text-xs font-medium shadow-sm">
                      consent_gate
                    </span>
                    <span className="text-xs text-muted-foreground/40">
                      &rarr;
                    </span>
                    <span className="rounded-lg border bg-card px-3 py-1.5 font-mono text-xs font-medium shadow-sm">
                      phase_router
                    </span>
                  </div>

                  {/* Connector */}
                  <div className="flex justify-center py-2">
                    <div className="h-4 w-px bg-border" />
                  </div>

                  {/* Subgraphs */}
                  <div className="flex flex-wrap justify-center gap-2">
                    {["Onboarding", "Active", "Re-engaging"].map((phase) => (
                      <span
                        key={phase}
                        className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-400"
                      >
                        {phase}
                      </span>
                    ))}
                  </div>

                  {/* Connector */}
                  <div className="flex justify-center py-2">
                    <div className="h-4 w-px bg-border" />
                  </div>

                  {/* Safety → output */}
                  <div className="flex items-center justify-center gap-2">
                    <span className="rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 font-mono text-xs font-medium text-red-700 shadow-sm dark:border-red-900 dark:bg-red-950 dark:text-red-400">
                      safety_classifier
                    </span>
                    <span className="text-xs text-muted-foreground/40">
                      &rarr;
                    </span>
                    <span className="rounded-lg border bg-card px-3 py-1.5 font-mono text-xs font-medium shadow-sm">
                      output
                    </span>
                  </div>
                </div>

                {/* ── Bottom: tools + infrastructure ── */}
                <div className="mt-6 flex flex-col items-center justify-between gap-4 sm:flex-row sm:items-start">
                  <div>
                    <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                      Tools
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {[
                        "set_goal",
                        "set_reminder",
                        "get_adherence",
                        "alert_clinician",
                      ].map((tool) => (
                        <span
                          key={tool}
                          className="rounded-md border bg-card px-2 py-1 font-mono text-[11px] text-muted-foreground"
                        >
                          {tool}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                      Infrastructure
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <span className="inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1 text-xs font-medium shadow-sm">
                        <Database className="size-3 text-cyan-500" />
                        SQLite
                      </span>
                      <span className="inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1 text-xs font-medium shadow-sm">
                        <Brain className="size-3 text-violet-500" />
                        Claude Haiku
                      </span>
                      <span className="inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1 text-xs font-medium shadow-sm">
                        <Activity className="size-3 text-emerald-500" />
                        LangSmith
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          </motion.section>

          {/* ── AI Integration ────────────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.h2
              variants={fadeInUp}
              className="text-2xl font-bold tracking-tight"
            >
              AI Integration
            </motion.h2>
            <motion.div
              variants={fadeInUp}
              className="mt-4 grid gap-4 sm:grid-cols-3"
            >
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-violet-100 dark:bg-violet-950">
                    <Brain className="size-5 text-violet-600 dark:text-violet-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <CardTitle className="text-sm">Claude Haiku 4.5</CardTitle>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Conversation generation (temp 0.7) and safety classification
                    (temp 0.0) via langchain_anthropic. Streaming responses over
                    SSE.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-950">
                    <Workflow className="size-5 text-emerald-600 dark:text-emerald-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <CardTitle className="text-sm">LangGraph Agent</CardTitle>
                  <p className="mt-1 text-xs text-muted-foreground">
                    17-node stateful graph with 3 phase subgraphs, deterministic
                    conditional routing, and checkpointed conversation state.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-950">
                    <Wrench className="size-5 text-amber-600 dark:text-amber-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <CardTitle className="text-sm">5 Autonomous Tools</CardTitle>
                  <p className="mt-1 text-xs text-muted-foreground">
                    set_goal, set_reminder, get_program_summary,
                    get_adherence_summary, alert_clinician — bound per-phase so
                    the LLM only accesses what&apos;s appropriate.
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          </motion.section>

          {/* ── Design Decisions ──────────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.h2
              variants={fadeInUp}
              className="text-2xl font-bold tracking-tight"
            >
              Design Decisions
            </motion.h2>
            <motion.p
              variants={fadeInUp}
              className="mt-2 text-sm text-muted-foreground"
            >
              The decisions that shaped the architecture — each one is a
              trade-off I evaluated.
            </motion.p>
            <motion.div variants={stagger} className="mt-6 space-y-3">
              {DESIGN_DECISIONS.map((item) => (
                <motion.div key={item.title} variants={fadeInUp}>
                  <Card>
                    <CardContent className="flex items-start gap-4 pt-5">
                      <div
                        className={`flex size-10 shrink-0 items-center justify-center rounded-lg ${item.color}`}
                      >
                        <item.icon className="size-5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="text-sm font-semibold">{item.title}</p>
                          <span className="text-xs text-muted-foreground">
                            — {item.decision}
                          </span>
                        </div>
                        <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                          {item.rationale}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </motion.section>

          {/* ── Testing ──────────────────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.h2
              variants={fadeInUp}
              className="text-2xl font-bold tracking-tight"
            >
              Testing
            </motion.h2>
            <motion.div
              variants={stagger}
              className="mt-6 grid gap-4 sm:grid-cols-2"
            >
              <motion.div variants={fadeInUp}>
                <Card className="h-full">
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-sm">
                      <TestTube className="size-4 text-emerald-500" />
                      701 Tests
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-xs text-muted-foreground">
                    <p>
                      Full coverage across safety classification, phase routing,
                      tool execution, API endpoints, graph traversal, and
                      consent enforcement.
                    </p>
                    <p>
                      Includes end-to-end journey tests from PENDING through all
                      5 phases and back, plus concurrent patient isolation
                      checks.
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
              <motion.div variants={fadeInUp}>
                <Card className="h-full">
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-sm">
                      <Shield className="size-4 text-red-500" />
                      113 Adversarial Prompts
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-xs text-muted-foreground">
                    <p>
                      Parametrized adversarial suite covering prompt injection,
                      clinical boundary violations, crisis scenario detection,
                      and identity manipulation attempts.
                    </p>
                    <p>
                      Three-layer defense: input sanitization, system prompt
                      isolation, and output validation via the two-tier
                      classifier.
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            </motion.div>
          </motion.section>

          {/* ── Trade-offs ────────────────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
            className="pb-10"
          >
            <motion.h2
              variants={fadeInUp}
              className="text-2xl font-bold tracking-tight"
            >
              Trade-offs
            </motion.h2>
            <motion.p
              variants={fadeInUp}
              className="mt-2 text-sm text-muted-foreground"
            >
              Intentional scoping decisions for a demo context — each one has a
              clear production path.
            </motion.p>
            <motion.div variants={fadeInUp} className="mt-4">
              <Card>
                <CardContent className="pt-5">
                  <ul className="space-y-2.5 text-sm text-muted-foreground">
                    <li className="flex items-start gap-2">
                      <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-amber-500" />
                      <span>
                        <strong className="text-foreground">
                          SQLite over PostgreSQL
                        </strong>{" "}
                        — simplified deployment for demo; production would use
                        Postgres with connection pooling
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-amber-500" />
                      <span>
                        <strong className="text-foreground">
                          In-memory checkpointer
                        </strong>{" "}
                        — sufficient for demo conversations; production would
                        use persistent state storage
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-amber-500" />
                      <span>
                        <strong className="text-foreground">
                          Manual re-engagement trigger
                        </strong>{" "}
                        — the re-engagement flow is fully built and testable;
                        production would wire it to a cron scheduler
                      </span>
                    </li>
                  </ul>
                </CardContent>
              </Card>
            </motion.div>
          </motion.section>
        </div>
      </ScrollArea>
    </div>
  );
}
