# Senior AI-First Software Engineer Assessment: Starter Files

This zip contains:

- `assessment-brief.pdf`: the brief. Start here.
- `seed.json`: the seed data your app loads on startup.
- `README.md`: this file, including the rules report format.

## About the seed data

- "Now" for the seed is **2026-11-11T15:00:00Z** (Wednesday, November 11, 2026, 9:00 AM Chicago). Your app reads "now" from `APP_NOW` and defaults to this value.
- The company time zone is America/Chicago. All timestamps in the file are UTC.
- Weeks are named by their Monday in company time (`week_start`), for example `2026-11-02`.
- Dates without a time (`due_date`) are calendar dates in company time.
- `source` on an Issue links it to a Measurable and week. `source_issue_id` on a To-Do links it to an Issue.
- The two meetings in `meetings` have already ended. Their summaries are part of the rules report.
- Keep the ids from `seed.json` (`u1`, `m1`, `t12`, ...). The rules report is keyed by them.

## Rules report format

Your rules report command prints this JSON for the current `APP_NOW`, computed on a freshly seeded database (no data added while testing). We will also run it at other dates, so compute every value from the data.

- Include every team, and every Measurable with all 13 weeks ending with the current week (Aug 17 to Nov 9 at the default `APP_NOW`).
- Include every one of those weeks in `todo_completion`. A week with nothing due is `null`.
- "Today" (for overdue To-Dos and past-due Milestones) is the date of `APP_NOW` in company time.
- Status values are `on_track`, `off_track` or `pending`. Rock status is `on_track`, `off_track` or `complete`.
- Percentages are whole numbers, rounded half up. Ratings have one decimal, rounded half up.
- Lists of ids are sorted as plain strings (`t12` before `t30`), except `issue_order`, which lists unsolved Issues in Issue order.
- `meetings` covers ended meetings, keyed by meeting id. `scorecard_week` is the week the meeting reviewed. `rating` is `null` if no one rated.

```json
{
  "now": "<APP_NOW, ISO 8601 UTC>",
  "teams": {
    "<team_id>": {
      "measurable_status": {"<measurable_id>": {"<week_start>": "on_track | off_track | pending"}},
      "todo_completion": {"<week_start>": "null, or {due, done, rate_percent, meets_target}"},
      "overdue_todos": ["<todo_id>"],
      "rocks": {"<rock_id>": {"status": "on_track | off_track | complete", "progress_percent": 0}},
      "issue_order": ["<issue_id>"],
      "meetings": {
        "<meeting_id>": {
          "scorecard_week": "<week_start>",
          "measurable_status": {"<measurable_id>": "on_track | off_track | pending"},
          "issues_solved": ["<issue_id>"],
          "todos_created": ["<todo_id>"],
          "attendee_ids": ["<user_id>"],
          "rating": "number with one decimal, or null"
        }
      }
    }
  }
}
```

A `todo_completion` week that has To-Dos due looks like this:

```json
{"due": 4, "done": 3, "rate_percent": 75, "meets_target": false}
```

`meets_target` compares the exact ratio with 90%, not the rounded percent.
