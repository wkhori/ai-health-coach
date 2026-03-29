import { DEMO_MODE } from "./demo-data";
import { ToolCall } from "./types";

/** Only use demo responses when DEMO_MODE is active */
export { DEMO_MODE };

interface DemoResponse {
  content: string;
  toolCalls?: ToolCall[];
  phaseChange?: { from: string; to: string };
}

const sarahResponses: DemoResponse[] = [
  {
    content:
      "That's great to hear you're considering jogging! Based on your walking consistency, I think you're ready for a walk-jog progression. Let me pull up your adherence summary to see the full picture.",
    toolCalls: [
      {
        tool: "get_adherence_summary",
        args: { patient_id: "sarah-001", period: "last_7_days" },
        result: {
          streak: 12,
          completion_rate: 0.85,
          goals_on_track: 2,
          trend: "improving",
        },
        status: "complete",
      },
    ],
  },
  {
    content:
      "Your numbers look fantastic, Sarah! 85% completion rate and a 12-day streak. Here's what I'd suggest for adding jogging: start with a 5-minute jog in the middle of your 30-minute walk. Listen to your body \u2014 if it feels good, gradually increase the jogging intervals. How does that sound?",
  },
  {
    content:
      "I love your dedication! Remember, rest days are just as important as active days. Your body needs time to recover and adapt. Since you're at week 3 of your walking milestone, let's make sure we nail that before adding too much. Would you like to set a target for completing your current walking milestone this week?",
  },
  {
    content:
      "Looking at your stretching routine \u2014 you're making solid progress there too! You've completed the first two milestones. The next step is moving to 15-minute stretches 5 times a week. Pairing a good stretch with your walking cool-down could be a great way to build the habit. Want to try combining them?",
  },
  {
    content:
      "That's completely understandable, Sarah. Everyone has off days, and what matters is the overall trend \u2014 which for you is clearly upward! Let's focus on what feels manageable today. Even a 10-minute walk counts as a win. What feels right for you?",
  },
];

const marcusResponses: DemoResponse[] = [
  {
    content:
      "That's a great start, Marcus! It sounds like you have some experience with physical activity. Based on what you've shared, I think we could set up a goal that builds on your interests. Let me create an initial walking goal for you \u2014 it's a great foundation that works for almost everyone.",
    toolCalls: [
      {
        tool: "set_goal",
        args: {
          title: "Walk 20 minutes 3x/week",
          milestones: [
            { title: "Walk 10 min 2x/week", week: 1 },
            { title: "Walk 15 min 2x/week", week: 2 },
            { title: "Walk 15 min 3x/week", week: 3 },
            { title: "Walk 20 min 3x/week", week: 4 },
          ],
        },
        result: {
          id: "goal-m1",
          title: "Walk 20 minutes 3x/week",
          status: "active",
          confirmed: false,
        },
        status: "complete",
      },
    ],
  },
  {
    content:
      "I've set up a walking goal with gradual milestones over 4 weeks. We start small \u2014 just 10 minutes twice a week \u2014 and build from there. Does this feel like a good starting point, or would you like to adjust anything? Once you confirm, we'll start tracking your progress!",
  },
  {
    content:
      "Welcome aboard! Setting realistic goals is the most important first step. There's no rush \u2014 we'll find the right pace for you. What time of day works best for you to be active? Morning, afternoon, or evening?",
  },
  {
    content:
      "That's helpful to know! Scheduling your activity at a consistent time helps build the habit. Many people find it easier to stick with a morning routine before the day gets busy, but the best time is whatever works for you. Shall we set a reminder for your preferred time?",
  },
  {
    content:
      "Great question! The milestones are designed to be achievable so you build confidence along the way. Each week builds on the last, and if any week feels too easy or too challenging, we can adjust. The key is consistency over intensity. Ready to confirm your goal?",
  },
];

const elenaResponses: DemoResponse[] = [
  {
    content:
      "It's so good to hear from you, Elena! There's no judgment here \u2014 life happens, and the important thing is that you're back. Let me take a look at where things stand with your goals.",
    toolCalls: [
      {
        tool: "get_program_summary",
        args: { patient_id: "elena-001" },
        result: {
          active_goals: 0,
          paused_goals: 2,
          total_milestones_completed: 3,
          days_since_last_activity: 5,
          phase: "RE_ENGAGING",
        },
        status: "complete",
      },
    ],
  },
  {
    content:
      "I can see you made great progress before the break \u2014 3 milestones completed across your swimming and yoga goals! That foundation doesn't disappear. Would you like to resume where you left off, or should we dial things back a bit and rebuild gradually?",
  },
  {
    content:
      "That makes total sense. Starting fresh with a lighter load is a smart approach. How about we begin with just one activity this week? You could choose between swimming or yoga \u2014 whichever feels more appealing right now. We can add the second one back once you're in a rhythm.",
  },
  {
    content:
      "Swimming is a fantastic choice! The water is great for your body, and it sounds like you really enjoyed it before. Let's set a gentle re-start: how about 10 laps twice this week? Once that feels comfortable, we'll build back up to your previous level.",
    phaseChange: { from: "RE_ENGAGING", to: "ACTIVE" },
  },
  {
    content:
      "Welcome back to your active routine! I'm really glad you're here. Remember, you've already proven you can do this \u2014 you completed those early milestones before. Let's take it one day at a time. When would you like to schedule your first swim session?",
  },
];

export const demoResponses: Record<string, DemoResponse[]> = {
  sarah: sarahResponses,
  marcus: marcusResponses,
  elena: elenaResponses,
};

export async function simulateStream(
  text: string,
  onToken: (token: string) => void
): Promise<void> {
  const words = text.split(" ");
  for (let i = 0; i < words.length; i++) {
    await new Promise((resolve) =>
      setTimeout(resolve, 30 + Math.random() * 50)
    );
    onToken(words[i] + (i < words.length - 1 ? " " : ""));
  }
}
