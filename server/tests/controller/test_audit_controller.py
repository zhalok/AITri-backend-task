from datetime import datetime, timezone
from types import SimpleNamespace

from app.modules.audit.factory import get_audit_usecase


def event(**kw):
    base = dict(
        id=7, occurred_at=datetime(2026, 11, 25, 10, 0, tzinfo=timezone.utc), txid=501, table_name="scores", op="UPDATE",
        team_id="t1", row_key="m1|2026-11-02", actor_id="u3", old_row={"value": 9}, new_row={"value": 12},
    )
    return SimpleNamespace(**{**base, **kw})


def test_events_come_back_with_the_table_and_the_old_and_new_row(client, mock_usecase, actor):
    uc = mock_usecase(get_audit_usecase)
    uc.list_events.return_value = [event()]
    body = client.get("/api/audit-events").json()
    assert body == [{
        "id": 7, "occurred_at": "2026-11-25T10:00:00Z", "txid": 501, "table": "scores", "op": "UPDATE", "team_id": "t1",
        "row_key": "m1|2026-11-02", "actor_id": "u3", "old": {"value": 9}, "new": {"value": 12},
    }]


def test_the_filters_are_passed_on(client, mock_usecase, actor):
    uc = mock_usecase(get_audit_usecase)
    uc.list_events.return_value = []
    client.get("/api/audit-events?team_id=t1&table=issues&row_key=i1&actor_id=u2&before_id=40&limit=25")
    uc.list_events.assert_called_once_with(
        actor, team_id="t1", table_name="issues", row_key="i1", actor_id="u2", before_id=40, limit=25
    )


def test_the_page_size_is_limited_at_the_edge_of_the_api(client, mock_usecase):
    uc = mock_usecase(get_audit_usecase)
    assert client.get("/api/audit-events?limit=501").status_code == 422
    assert client.get("/api/audit-events?limit=0").status_code == 422
    uc.list_events.assert_not_called()
