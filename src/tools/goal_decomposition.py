"""Goal decomposition logic — generates 4-week progressive milestones.

For MVP, uses simple templates based on goal type + frequency.
No LLM needed for milestone generation.
"""

import structlog

logger = structlog.get_logger(__name__)

# Week progression multipliers — each week builds on the previous
_WEEK_LABELS = ["Foundation", "Building", "Strengthening", "Achievement"]
_INTENSITY_SCALE = [0.4, 0.6, 0.8, 1.0]  # fraction of full target


def generate_milestones(
    title: str,
    description: str,
    frequency: str,
    target_per_week: int,
) -> list[dict]:
    """Generate 4 weekly milestones for a goal.

    Args:
        title: Goal title (e.g., "Run a 5K")
        description: Goal description
        frequency: How often (e.g., "daily", "3 times per week")
        target_per_week: Number of sessions per week target

    Returns:
        List of 4 milestone dicts with title, description, week_number.
    """
    effective_target = max(target_per_week, 1)
    goal_title = title if title else "your goal"

    milestones = []
    for week_num in range(1, 5):
        idx = week_num - 1
        week_target = max(1, round(effective_target * _INTENSITY_SCALE[idx]))
        label = _WEEK_LABELS[idx]

        if week_num == 1:
            milestone_title = f"Week {week_num}: {label} — Start with {week_target} session(s)"
            milestone_desc = (
                f"Begin working toward {goal_title}. "
                f"Aim for {week_target} session(s) this week at a comfortable pace. "
                f"Focus on building the habit."
            )
        elif week_num == 2:
            milestone_title = f"Week {week_num}: {label} — Increase to {week_target} session(s)"
            milestone_desc = (
                f"Build on last week's progress toward {goal_title}. "
                f"Aim for {week_target} session(s) this week with slightly more intensity. "
                f"Start extending your duration or effort."
            )
        elif week_num == 3:
            milestone_title = f"Week {week_num}: {label} — Push to {week_target} session(s)"
            milestone_desc = (
                f"You're getting stronger! Work toward {goal_title} with "
                f"{week_target} session(s) this week. "
                f"Increase intensity or duration to challenge yourself."
            )
        else:  # week 4
            milestone_title = (
                f"Week {week_num}: {label} — Reach your target of {week_target} session(s)"
            )
            milestone_desc = (
                f"Final push toward {goal_title}! "
                f"Complete {week_target} session(s) this week at your target level. "
                f"Celebrate your progress!"
            )

        milestones.append(
            {
                "title": milestone_title,
                "description": milestone_desc,
                "week_number": week_num,
            }
        )

    logger.info(
        "milestones_generated",
        goal_title=title,
        target_per_week=target_per_week,
        milestone_count=len(milestones),
    )

    return milestones
