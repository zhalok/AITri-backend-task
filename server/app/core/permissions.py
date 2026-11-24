"""Role -> actions access control matrix (spec 2.4).

One action per endpoint. Each role lists exactly what it may do, so reading one role's
entry answers "what can this role do?". Anything not listed is denied.

Scope is expressed the same way, and the default is always the narrowest: an action such as
SOLVE_ISSUE only works in a team the user is a member of (a separate check, TeamScope, that the use case runs
after RBAC). Wider reach is a separate endpoint under /api/admin with its own action
(ANY_TEAM_SOLVE_ISSUE) that only Admins hold. Likewise LIST_MY_TEAMS vs LIST_ALL_TEAMS.
Facilitator-only and attendee-only rules depend on the specific meeting and live in MeetingService.
"""
from enum import StrEnum

from app.modules.user.models import Role


class Action(StrEnum):
    # Users / teams
    LIST_USERS = "list_users"  # narrow default: people in the caller's own teams
    LIST_ALL_USERS = "list_all_users"  # wide: everyone in the company
    LIST_MY_TEAMS = "list_my_teams"
    LIST_ALL_TEAMS = "list_all_teams"
    VIEW_TEAM = "view_team"
    LIST_TEAM_MEMBERS = "list_team_members"
    # Scorecard
    LIST_MEASURABLES = "list_measurables"
    VIEW_SCORECARD = "view_scorecard"
    EDIT_SCORE = "edit_score"
    # Rocks
    LIST_ROCKS = "list_rocks"
    # Issues
    LIST_ISSUES = "list_issues"
    CREATE_ISSUE = "create_issue"
    MAKE_ISSUE_FROM_SCORE = "make_issue_from_score"
    SET_ISSUE_PRIORITY = "set_issue_priority"
    SOLVE_ISSUE = "solve_issue"
    # To-Dos
    LIST_TODOS = "list_todos"
    CREATE_TODO = "create_todo"
    MARK_TODO_DONE = "mark_todo_done"
    UNDO_TODO_DONE = "undo_todo_done"
    # Meetings
    START_MEETING = "start_meeting"  # starter becomes facilitator
    VIEW_ACTIVE_MEETING = "view_active_meeting"
    VIEW_MEETING = "view_meeting"
    JOIN_MEETING = "join_meeting"
    ADVANCE_MEETING = "advance_meeting"  # + must be the facilitator
    END_MEETING = "end_meeting"  # + must be the facilitator
    RATE_MEETING = "rate_meeting"  # + must be an attendee
    # Wide scope: the same operations in ANY team, without membership (/api/admin/...). Admin only.
    ANY_TEAM_VIEW_TEAM = "any_team_view_team"
    ANY_TEAM_LIST_TEAM_MEMBERS = "any_team_list_team_members"
    ANY_TEAM_LIST_MEASURABLES = "any_team_list_measurables"
    ANY_TEAM_VIEW_SCORECARD = "any_team_view_scorecard"
    ANY_TEAM_EDIT_SCORE = "any_team_edit_score"
    ANY_TEAM_LIST_ROCKS = "any_team_list_rocks"
    ANY_TEAM_LIST_ISSUES = "any_team_list_issues"
    ANY_TEAM_CREATE_ISSUE = "any_team_create_issue"
    ANY_TEAM_MAKE_ISSUE_FROM_SCORE = "any_team_make_issue_from_score"
    ANY_TEAM_SET_ISSUE_PRIORITY = "any_team_set_issue_priority"
    ANY_TEAM_SOLVE_ISSUE = "any_team_solve_issue"
    ANY_TEAM_LIST_TODOS = "any_team_list_todos"
    ANY_TEAM_CREATE_TODO = "any_team_create_todo"
    ANY_TEAM_MARK_TODO_DONE = "any_team_mark_todo_done"
    ANY_TEAM_UNDO_TODO_DONE = "any_team_undo_todo_done"
    ANY_TEAM_START_MEETING = "any_team_start_meeting"
    ANY_TEAM_VIEW_ACTIVE_MEETING = "any_team_view_active_meeting"
    ANY_TEAM_VIEW_MEETING = "any_team_view_meeting"
    ANY_TEAM_JOIN_MEETING = "any_team_join_meeting"
    ANY_TEAM_ADVANCE_MEETING = "any_team_advance_meeting"
    ANY_TEAM_END_MEETING = "any_team_end_meeting"
    ANY_TEAM_RATE_MEETING = "any_team_rate_meeting"
    # Audit trail (Admin only, any team)
    LIST_AUDIT_EVENTS = "list_audit_events"
    # Capability (not an endpoint)
    BE_ASSIGNED_WORK = "be_assigned_work"  # may own Issues, To-Dos, Measurables, Rocks


OBSERVER_ACTIONS = frozenset({
    Action.LIST_USERS, Action.LIST_MY_TEAMS, Action.VIEW_TEAM, Action.LIST_TEAM_MEMBERS,
    Action.LIST_MEASURABLES, Action.VIEW_SCORECARD, Action.LIST_ROCKS, Action.LIST_ISSUES,
    Action.LIST_TODOS, Action.VIEW_ACTIVE_MEETING, Action.VIEW_MEETING, Action.JOIN_MEETING,
})

TEAM_MEMBER_ACTIONS = OBSERVER_ACTIONS | frozenset({
    Action.EDIT_SCORE, Action.CREATE_ISSUE, Action.MAKE_ISSUE_FROM_SCORE, Action.SET_ISSUE_PRIORITY,
    Action.SOLVE_ISSUE, Action.CREATE_TODO, Action.MARK_TODO_DONE, Action.UNDO_TODO_DONE,
    Action.START_MEETING, Action.ADVANCE_MEETING, Action.END_MEETING, Action.RATE_MEETING,
    Action.BE_ASSIGNED_WORK,
})

# Narrow action -> its wide (any team) counterpart.
ANY_TEAM_OF: dict[Action, Action] = {
    Action.VIEW_TEAM: Action.ANY_TEAM_VIEW_TEAM,
    Action.LIST_TEAM_MEMBERS: Action.ANY_TEAM_LIST_TEAM_MEMBERS,
    Action.LIST_MEASURABLES: Action.ANY_TEAM_LIST_MEASURABLES,
    Action.VIEW_SCORECARD: Action.ANY_TEAM_VIEW_SCORECARD,
    Action.EDIT_SCORE: Action.ANY_TEAM_EDIT_SCORE,
    Action.LIST_ROCKS: Action.ANY_TEAM_LIST_ROCKS,
    Action.LIST_ISSUES: Action.ANY_TEAM_LIST_ISSUES,
    Action.CREATE_ISSUE: Action.ANY_TEAM_CREATE_ISSUE,
    Action.MAKE_ISSUE_FROM_SCORE: Action.ANY_TEAM_MAKE_ISSUE_FROM_SCORE,
    Action.SET_ISSUE_PRIORITY: Action.ANY_TEAM_SET_ISSUE_PRIORITY,
    Action.SOLVE_ISSUE: Action.ANY_TEAM_SOLVE_ISSUE,
    Action.LIST_TODOS: Action.ANY_TEAM_LIST_TODOS,
    Action.CREATE_TODO: Action.ANY_TEAM_CREATE_TODO,
    Action.MARK_TODO_DONE: Action.ANY_TEAM_MARK_TODO_DONE,
    Action.UNDO_TODO_DONE: Action.ANY_TEAM_UNDO_TODO_DONE,
    Action.START_MEETING: Action.ANY_TEAM_START_MEETING,
    Action.VIEW_ACTIVE_MEETING: Action.ANY_TEAM_VIEW_ACTIVE_MEETING,
    Action.VIEW_MEETING: Action.ANY_TEAM_VIEW_MEETING,
    Action.JOIN_MEETING: Action.ANY_TEAM_JOIN_MEETING,
    Action.ADVANCE_MEETING: Action.ANY_TEAM_ADVANCE_MEETING,
    Action.END_MEETING: Action.ANY_TEAM_END_MEETING,
    Action.RATE_MEETING: Action.ANY_TEAM_RATE_MEETING,
}

ADMIN_ACTIONS = (
    TEAM_MEMBER_ACTIONS
    | frozenset({Action.LIST_ALL_TEAMS, Action.LIST_ALL_USERS, Action.LIST_AUDIT_EVENTS})
    | frozenset(ANY_TEAM_OF.values())
)

ROLE_ACTIONS: dict[str, frozenset[Action]] = {
    Role.OBSERVER: OBSERVER_ACTIONS,
    Role.TEAM_MEMBER: TEAM_MEMBER_ACTIONS,
    Role.ADMIN: ADMIN_ACTIONS,
}

assert ROLE_ACTIONS[Role.ADMIN] == frozenset(Action), "Admin can do everything (spec 2.4)"
assert all(a in ROLE_ACTIONS[Role.TEAM_MEMBER] or a in OBSERVER_ACTIONS for a in ANY_TEAM_OF), "narrow actions belong to members"


def role_can(role: str, action: Action) -> bool:
    """The checker: does this role have this action? Pure; knows nothing about users or teams."""
    return action in ROLE_ACTIONS.get(role, frozenset())
