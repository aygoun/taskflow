import pytest


class TestSortByPriority:
    def test_sort_priority_desc_high_first(self, client):
        client.post("/api/tasks", json={"title": "Low task", "priority": "low"})
        client.post("/api/tasks", json={"title": "High task", "priority": "high"})
        client.post("/api/tasks", json={"title": "Medium task", "priority": "medium"})
        client.post("/api/tasks", json={"title": "Another high", "priority": "high"})

        resp = client.get("/api/tasks?sort_by=priority&sort_order=desc")
        assert resp.status_code == 200
        data = resp.json()
        priorities = [t["priority"] for t in data]
        assert priorities == ["high", "high", "medium", "low"]

    def test_sort_priority_asc_low_first(self, client):
        client.post("/api/tasks", json={"title": "High task", "priority": "high"})
        client.post("/api/tasks", json={"title": "Low task", "priority": "low"})
        client.post("/api/tasks", json={"title": "Medium task", "priority": "medium"})

        resp = client.get("/api/tasks?sort_by=priority&sort_order=asc")
        assert resp.status_code == 200
        data = resp.json()
        priorities = [t["priority"] for t in data]
        assert priorities == ["low", "medium", "high"]


class TestSortByTitle:
    def test_sort_title_asc(self, client):
        client.post("/api/tasks", json={"title": "Charlie"})
        client.post("/api/tasks", json={"title": "Alpha"})
        client.post("/api/tasks", json={"title": "Bravo"})

        resp = client.get("/api/tasks?sort_by=title&sort_order=asc")
        assert resp.status_code == 200
        titles = [t["title"] for t in resp.json()]
        assert titles == ["Alpha", "Bravo", "Charlie"]

    def test_sort_title_desc(self, client):
        client.post("/api/tasks", json={"title": "Charlie"})
        client.post("/api/tasks", json={"title": "Alpha"})
        client.post("/api/tasks", json={"title": "Bravo"})

        resp = client.get("/api/tasks?sort_by=title&sort_order=desc")
        assert resp.status_code == 200
        titles = [t["title"] for t in resp.json()]
        assert titles == ["Charlie", "Bravo", "Alpha"]


class TestSortByDueDate:
    def test_sort_due_date_asc(self, client):
        client.post("/api/tasks", json={"title": "Late", "due_date": "2025-12-31"})
        client.post("/api/tasks", json={"title": "Early", "due_date": "2025-01-01"})

        resp = client.get("/api/tasks?sort_by=due_date&sort_order=asc")
        assert resp.status_code == 200
        titles = [t["title"] for t in resp.json()]
        assert titles[0] == "Early"


class TestSortDefault:
    def test_default_sort_is_created_at_desc(self, client):
        client.post("/api/tasks", json={"title": "First"})
        client.post("/api/tasks", json={"title": "Second"})

        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        data = resp.json()
        # Default is created_at desc, so newest first
        assert data[0]["title"] == "Second"
        assert data[1]["title"] == "First"


class TestSortValidation:
    def test_invalid_sort_by_returns_400(self, client):
        resp = client.get("/api/tasks?sort_by=invalid")
        assert resp.status_code == 400

    def test_invalid_sort_order_returns_400(self, client):
        resp = client.get("/api/tasks?sort_order=invalid")
        assert resp.status_code == 400

    def test_valid_sort_by_created_at(self, client):
        client.post("/api/tasks", json={"title": "Task"})
        resp = client.get("/api/tasks?sort_by=created_at&sort_order=asc")
        assert resp.status_code == 200
