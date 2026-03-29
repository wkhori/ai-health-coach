"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Heart,
  ArrowLeft,
  Brain,
  Shield,
  GitBranch,
  Database,
  Zap,
  TestTube,
  Code2,
  MessageSquare,
  Target,
  Clock,
  AlertTriangle,
  Layers,
  Workflow,
  Lock,
  BarChart3,
  Bot,
  Gauge,
  Network,
  Play,
  Wrench,
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
const METRICS = [
  { label: "Lines of Code", value: "5,000+", icon: Code2, color: "bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400" },
  { label: "Tests Passing", value: "701", icon: TestTube, color: "bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400" },
  { label: "Adversarial Prompts", value: "113", icon: Shield, color: "bg-red-100 dark:bg-red-950 text-red-600 dark:text-red-400" },
  { label: "Safety Rules", value: "24", icon: Lock, color: "bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400" },
  { label: "AI Tools", value: "5", icon: Wrench, color: "bg-violet-100 dark:bg-violet-950 text-violet-600 dark:text-violet-400" },
  { label: "API Endpoints", value: "14", icon: Network, color: "bg-cyan-100 dark:bg-cyan-950 text-cyan-600 dark:text-cyan-400" },
  { label: "Database Tables", value: "10", icon: Database, color: "bg-orange-100 dark:bg-orange-950 text-orange-600 dark:text-orange-400" },
  { label: "Graph Nodes", value: "17", icon: Workflow, color: "bg-pink-100 dark:bg-pink-950 text-pink-600 dark:text-pink-400" },
];

const TECH_STACK = [
  { name: "Python 3.12+", role: "Backend Language", icon: Code2, color: "bg-blue-100 dark:bg-blue-950 text-blue-600" },
  { name: "LangGraph", role: "Agent Framework", icon: Workflow, color: "bg-emerald-100 dark:bg-emerald-950 text-emerald-600" },
  { name: "Claude Haiku 4.5", role: "LLM", icon: Brain, color: "bg-violet-100 dark:bg-violet-950 text-violet-600" },
  { name: "FastAPI", role: "API Server", icon: Zap, color: "bg-amber-100 dark:bg-amber-950 text-amber-600" },
  { name: "Next.js 16", role: "Frontend Framework", icon: Layers, color: "bg-zinc-100 dark:bg-zinc-900 text-zinc-600" },
  { name: "SQLite", role: "Database", icon: Database, color: "bg-cyan-100 dark:bg-cyan-950 text-cyan-600" },
  { name: "SSE Streaming", role: "Real-time Chat", icon: MessageSquare, color: "bg-pink-100 dark:bg-pink-950 text-pink-600" },
  { name: "pytest", role: "Testing (701 tests)", icon: TestTube, color: "bg-red-100 dark:bg-red-950 text-red-600" },
];

const INNOVATIONS = [
  {
    title: "Two-Tier Safety Classifier",
    description: "Every outbound message passes through a regex pre-filter (Tier 1) and an LLM classifier (Tier 2). Crisis signals trigger hard-coded safe responses with the 988 Lifeline — the LLM never generates crisis text.",
    icon: Shield,
    color: "bg-red-100 dark:bg-red-950 text-red-600 dark:text-red-400",
  },
  {
    title: "Deterministic Phase Routing",
    description: "The 5-phase state machine (PENDING → ONBOARDING → ACTIVE → RE_ENGAGING → DORMANT) is 100% application code. Phase transitions are never LLM-decided, ensuring predictable patient journeys.",
    icon: GitBranch,
    color: "bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400",
  },
  {
    title: "Autonomous Tool Calling",
    description: "The LLM independently decides when to call tools like set_goal, get_adherence_summary, and alert_clinician. Tools are bound per-phase — onboarding patients can only set goals, not check adherence.",
    icon: Bot,
    color: "bg-violet-100 dark:bg-violet-950 text-violet-600 dark:text-violet-400",
  },
  {
    title: "Consent-Gated Interactions",
    description: "Every single interaction verifies consent before any coaching occurs. Not cached, not assumed. The consent gate runs on every request as a graph node before any subgraph is invoked.",
    icon: Lock,
    color: "bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400",
  },
  {
    title: "Clinician Dashboard & Alerts",
    description: "Real-time multi-patient triage view with phase distribution, adherence tracking, and safety alerts. Crisis detection auto-generates urgent clinician alerts visible in the dashboard.",
    icon: BarChart3,
    color: "bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400",
  },
  {
    title: "113 Adversarial Prompt Tests",
    description: "Systematic adversarial testing covering prompt injection, clinical boundary violations, crisis scenarios, and edge cases. Safety false-negative rate target: <1%.",
    icon: AlertTriangle,
    color: "bg-orange-100 dark:bg-orange-950 text-orange-600 dark:text-orange-400",
  },
];

const CONSTRAINTS = [
  { label: "Safety FN Rate", value: "< 1%", description: "Critical safety signals are never missed" },
  { label: "Safety FP Rate", value: "< 10%", description: "Minimizes unnecessary content blocking" },
  { label: "Rate Limit", value: "10 msg/min", description: "Per-user sliding window protection" },
  { label: "Re-engage Backoff", value: "Day 2, 5, 7", description: "Exponential backoff before dormancy" },
  { label: "Context Window", value: "~1,800 tokens", description: "Summarize every 6 turns to stay lean" },
  { label: "Max Attempts", value: "3", description: "Re-engagement attempts before DORMANT" },
];

const ADRS = [
  {
    decision: "Agent Framework",
    choice: "LangGraph over raw LangChain",
    rationale: "LangGraph provides first-class support for stateful, multi-step agent workflows with checkpointing, conditional routing, and subgraph composition — essential for a phase-based coaching system.",
  },
  {
    decision: "Safety Architecture",
    choice: "Two-tier (Rules + LLM) over LLM-only",
    rationale: "Tier 1 regex catches obvious cases in <1ms. Tier 2 LLM handles ambiguity. This cuts LLM calls by ~70% while maintaining <1% false negative rate on critical safety signals.",
  },
  {
    decision: "Phase Routing",
    choice: "Deterministic code over LLM-decided",
    rationale: "Healthcare requires predictable behavior. LLM-decided routing would introduce non-determinism in patient care pathways. Application code reads state and returns a node name — no AI involved.",
  },
  {
    decision: "Streaming Protocol",
    choice: "SSE over WebSocket",
    rationale: "SSE is simpler, works through proxies/CDNs, auto-reconnects, and is sufficient for server→client token streaming. WebSocket bidirectionality isn't needed for chat.",
  },
  {
    decision: "Crisis Responses",
    choice: "Hard-coded over LLM-generated",
    rationale: "Crisis responses include specific hotline numbers (988 Lifeline, Crisis Text Line). LLM hallucination risk is unacceptable here — these are static, verified strings.",
  },
];

const GRAPH_NODES = [
  { name: "load_context", type: "setup" },
  { name: "consent_gate", type: "gate" },
  { name: "phase_router", type: "router" },
  { name: "onboarding_subgraph", type: "subgraph" },
  { name: "active_subgraph", type: "subgraph" },
  { name: "re_engaging_subgraph", type: "subgraph" },
  { name: "safety_classifier", type: "safety" },
  { name: "output_final", type: "output" },
  { name: "rewrite_message", type: "output" },
  { name: "block_and_alert", type: "output" },
  { name: "log_and_respond", type: "output" },
  { name: "check_phase_transition", type: "gate" },
];

const NODE_COLORS: Record<string, string> = {
  setup: "bg-blue-500",
  gate: "bg-amber-500",
  router: "bg-violet-500",
  subgraph: "bg-emerald-500",
  safety: "bg-red-500",
  output: "bg-zinc-400 dark:bg-zinc-600",
};

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
              How It Was Built
            </h1>
          </div>
        </div>
        <Link href="/">
          <Button variant="ghost" size="sm" className="gap-1.5 text-muted-foreground">
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
              An AI-powered accountability partner that helps patients stick to their
              home exercise programs through goal-setting, safety-first coaching,
              and intelligent re-engagement.
            </motion.p>
            <motion.div variants={fadeInUp} className="mt-6 flex items-center justify-center gap-3">
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

          {/* ── Demo Video Placeholder ────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.div variants={fadeInUp}>
              <Card className="overflow-hidden">
                <div className="flex aspect-video items-center justify-center bg-muted/50">
                  <div className="text-center">
                    <div className="mx-auto mb-3 flex size-16 items-center justify-center rounded-full bg-muted">
                      <Play className="size-8 text-muted-foreground" />
                    </div>
                    <p className="text-sm font-medium text-muted-foreground">
                      Demo Video
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground/60">
                      5-minute walkthrough coming soon
                    </p>
                  </div>
                </div>
              </Card>
            </motion.div>
          </motion.section>

          {/* ── What It Does ──────────────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.h2 variants={fadeInUp} className="text-2xl font-bold tracking-tight">
              The Problem
            </motion.h2>
            <motion.div variants={fadeInUp} className="mt-4 space-y-4 text-muted-foreground">
              <p>
                Healthcare providers prescribe home exercise programs (HEPs) to patients,
                but <strong className="text-foreground">adherence is notoriously low</strong>.
                Patients fall off their programs when they don&apos;t feel supported between visits.
                Clinicians are already stretched thin and don&apos;t have bandwidth for regular
                motivational check-ins with every patient.
              </p>
              <p>
                This project builds an <strong className="text-foreground">AI-powered accountability partner</strong> that
                proactively engages patients through onboarding, goal-setting, and follow-up —
                without crossing into clinical advice. Every response passes through a two-tier
                safety classifier. Clinical content triggers automatic redirects to the care team.
                Crisis signals trigger hard-coded safe responses with hotline numbers.
              </p>
            </motion.div>
          </motion.section>

          {/* ── AI Integration ────────────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.h2 variants={fadeInUp} className="text-2xl font-bold tracking-tight">
              AI Integration
            </motion.h2>
            <motion.div variants={fadeInUp} className="mt-4 grid gap-4 sm:grid-cols-3">
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-violet-100 dark:bg-violet-950">
                    <Brain className="size-5 text-violet-600 dark:text-violet-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <CardTitle className="text-sm">Claude Haiku 4.5</CardTitle>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Conversation generation and safety classification via langchain_anthropic.
                    Temperature 0.7 for coaching, 0.0 for safety.
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
                    17-node stateful graph with 3 phase subgraphs, conditional routing,
                    and checkpointed conversation state.
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
                    set_goal, set_reminder, get_program_summary, get_adherence_summary,
                    alert_clinician — the LLM decides when to call them.
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          </motion.section>

          {/* ── Architecture Diagram ──────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.h2 variants={fadeInUp} className="text-2xl font-bold tracking-tight">
              System Architecture
            </motion.h2>
            <motion.p variants={fadeInUp} className="mt-2 text-sm text-muted-foreground">
              The LangGraph main graph processes every patient interaction through this pipeline.
            </motion.p>
            <motion.div variants={fadeInUp} className="mt-6">
              <Card className="overflow-x-auto p-6">
                <div className="flex flex-wrap items-center gap-2 text-xs font-medium">
                  {GRAPH_NODES.map((node, i) => (
                    <div key={node.name} className="flex items-center gap-2">
                      <div className="flex items-center gap-1.5 rounded-lg border bg-card px-3 py-2 shadow-sm">
                        <span className={`size-2 rounded-full ${NODE_COLORS[node.type]}`} />
                        <span className="font-mono">{node.name}</span>
                      </div>
                      {i < GRAPH_NODES.length - 1 && (
                        <span className="text-muted-foreground/40">→</span>
                      )}
                    </div>
                  ))}
                </div>
                <div className="mt-4 flex flex-wrap gap-4 text-[10px] text-muted-foreground">
                  {Object.entries(NODE_COLORS).map(([type, color]) => (
                    <div key={type} className="flex items-center gap-1.5">
                      <span className={`size-2 rounded-full ${color}`} />
                      <span className="capitalize">{type}</span>
                    </div>
                  ))}
                </div>
              </Card>
            </motion.div>
          </motion.section>

          {/* ── By the Numbers ────────────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.h2 variants={fadeInUp} className="text-2xl font-bold tracking-tight">
              By the Numbers
            </motion.h2>
            <motion.div
              variants={stagger}
              className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4"
            >
              {METRICS.map((m) => (
                <motion.div key={m.label} variants={fadeInUp}>
                  <Card className="text-center">
                    <CardContent className="pt-5">
                      <div className={`mx-auto mb-3 flex size-10 items-center justify-center rounded-lg ${m.color}`}>
                        <m.icon className="size-5" />
                      </div>
                      <p className="text-2xl font-bold tracking-tight">{m.value}</p>
                      <p className="mt-0.5 text-xs text-muted-foreground">{m.label}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </motion.section>

          {/* ── Tech Stack ────────────────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.h2 variants={fadeInUp} className="text-2xl font-bold tracking-tight">
              Tech Stack
            </motion.h2>
            <motion.div
              variants={stagger}
              className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4"
            >
              {TECH_STACK.map((t) => (
                <motion.div key={t.name} variants={fadeInUp}>
                  <Card>
                    <CardContent className="flex items-center gap-3 pt-5">
                      <div className={`flex size-9 shrink-0 items-center justify-center rounded-lg ${t.color}`}>
                        <t.icon className="size-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">{t.name}</p>
                        <p className="truncate text-xs text-muted-foreground">{t.role}</p>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </motion.section>

          {/* ── Innovation Highlights ─────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.h2 variants={fadeInUp} className="text-2xl font-bold tracking-tight">
              Innovation Highlights
            </motion.h2>
            <motion.div
              variants={stagger}
              className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
            >
              {INNOVATIONS.map((item) => (
                <motion.div key={item.title} variants={fadeInUp}>
                  <Card className="h-full">
                    <CardHeader className="pb-2">
                      <div className={`flex size-10 items-center justify-center rounded-lg ${item.color}`}>
                        <item.icon className="size-5" />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <CardTitle className="text-sm">{item.title}</CardTitle>
                      <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                        {item.description}
                      </p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </motion.section>

          {/* ── Operating Constraints ─────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.h2 variants={fadeInUp} className="text-2xl font-bold tracking-tight">
              Operating Constraints
            </motion.h2>
            <motion.div
              variants={stagger}
              className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3"
            >
              {CONSTRAINTS.map((c) => (
                <motion.div key={c.label} variants={fadeInUp}>
                  <Card>
                    <CardContent className="pt-5">
                      <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
                        {c.value}
                      </p>
                      <p className="text-sm font-medium">{c.label}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{c.description}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </motion.section>

          {/* ── Architecture Decisions ────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.h2 variants={fadeInUp} className="text-2xl font-bold tracking-tight">
              Architecture Decisions
            </motion.h2>
            <motion.div variants={stagger} className="mt-6 space-y-3">
              {ADRS.map((adr) => (
                <motion.div key={adr.decision} variants={fadeInUp}>
                  <Card>
                    <CardContent className="flex flex-col gap-2 pt-5 sm:flex-row sm:items-start sm:gap-6">
                      <div className="shrink-0">
                        <Badge variant="outline" className="text-xs font-medium">
                          {adr.decision}
                        </Badge>
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium">{adr.choice}</p>
                        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                          {adr.rationale}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </motion.section>

          {/* ── Security & Code Quality ───────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
          >
            <motion.h2 variants={fadeInUp} className="text-2xl font-bold tracking-tight">
              Security & Code Quality
            </motion.h2>
            <motion.div variants={stagger} className="mt-6 grid gap-4 sm:grid-cols-2">
              <motion.div variants={fadeInUp}>
                <Card className="h-full">
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-sm">
                      <Shield className="size-4 text-red-500" />
                      Three-Layer Prompt Defense
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-xs text-muted-foreground">
                    <p><strong className="text-foreground">Layer 1:</strong> Input sanitization strips control characters and detects injection patterns</p>
                    <p><strong className="text-foreground">Layer 2:</strong> System prompt isolation with defensive instructions and clear role boundaries</p>
                    <p><strong className="text-foreground">Layer 3:</strong> Output validation via two-tier safety classifier on every generated message</p>
                  </CardContent>
                </Card>
              </motion.div>
              <motion.div variants={fadeInUp}>
                <Card className="h-full">
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-sm">
                      <Gauge className="size-4 text-emerald-500" />
                      Testing Coverage
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-xs text-muted-foreground">
                    <p><strong className="text-foreground">701 tests</strong> covering safety, routing, tools, API, graph, consent, and adversarial scenarios</p>
                    <p><strong className="text-foreground">113 adversarial prompts</strong> testing injection attacks, clinical boundaries, crisis detection, and edge cases</p>
                    <p><strong className="text-foreground">Full journey tests</strong> from PENDING through all 5 phases and back</p>
                  </CardContent>
                </Card>
              </motion.div>
            </motion.div>
          </motion.section>

          {/* ── Known Limitations ─────────────────────── */}
          <motion.section
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
            className="pb-10"
          >
            <motion.h2 variants={fadeInUp} className="text-2xl font-bold tracking-tight">
              Known Limitations & Next Steps
            </motion.h2>
            <motion.div variants={fadeInUp} className="mt-4">
              <Card>
                <CardContent className="grid gap-4 pt-5 sm:grid-cols-2">
                  <div>
                    <p className="text-sm font-medium">Current Trade-offs</p>
                    <ul className="mt-2 space-y-1.5 text-xs text-muted-foreground">
                      <li className="flex items-start gap-2">
                        <span className="mt-1 size-1.5 shrink-0 rounded-full bg-amber-500" />
                        SQLite for demo simplicity — production would use PostgreSQL
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 size-1.5 shrink-0 rounded-full bg-amber-500" />
                        In-memory checkpointer — production would use AsyncPostgresSaver
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 size-1.5 shrink-0 rounded-full bg-amber-500" />
                        Scheduled follow-ups designed but not wired to cron trigger
                      </li>
                    </ul>
                  </div>
                  <div>
                    <p className="text-sm font-medium">What I&apos;d Build Next</p>
                    <ul className="mt-2 space-y-1.5 text-xs text-muted-foreground">
                      <li className="flex items-start gap-2">
                        <span className="mt-1 size-1.5 shrink-0 rounded-full bg-emerald-500" />
                        Clinician-visible conversation summaries in dashboard
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 size-1.5 shrink-0 rounded-full bg-emerald-500" />
                        Outcome analytics — adherence trends over time
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 size-1.5 shrink-0 rounded-full bg-emerald-500" />
                        FHIR integration for EHR interoperability
                      </li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </motion.section>
        </div>
      </ScrollArea>
    </div>
  );
}
