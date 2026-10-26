import pytest


class TestHealth:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestCreateTask:
    def test_create_task(self, client):
        resp = client.post("/api/tasks", json={"title": "Buy groceries", "priority": "high"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Buy groceries"
        assert data["priority"] == "high"
        assert data["completed"] is False
        assert "id" in data

    def test_create_task_with_description(self, client):
        resp = client.post(
            "/api/tasks",
            json={"title": "Write report", "description": "Q4 summary", "priority": "medium"},
        )
        assert resp.status_code == 201
        assert resp.json()["description"] == "Q4 summary"

    def test_create_task_invalid_priority(self, client):
        resp = client.post("/api/tasks", json={"title": "Test", "priority": "urgent"})
        assert resp.status_code == 400

    def test_create_task_missing_title(self, client):
        resp = client.post("/api/tasks", json={"priority": "low"})
        assert resp.status_code == 422


class TestListTasks:
    def test_list_empty(self, client):
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_tasks(self, client):
        client.post("/api/tasks", json={"title": "Task 1"})
        client.post("/api/tasks", json={"title": "Task 2"})
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_filter_by_completed(self, client):
        client.post("/api/tasks", json={"title": "Done task"})
        client.post("/api/tasks", json={"title": "Open task"})
        # Complete the first task
        tasks = client.get("/api/tasks").json()
        client.patch(f"/api/tasks/{tasks[0]['id']}", json={"completed": True})

        resp = client.get("/api/tasks?completed=true")
        assert len(resp.json()) == 1
        assert resp.json()[0]["completed"] is True

        resp = client.get("/api/tasks?completed=false")
        assert len(resp.json()) == 1
        assert resp.json()[0]["completed"] is False

    def test_filter_by_priority(self, client):
        client.post("/api/tasks", json={"title": "High", "priority": "high"})
        client.post("/api/tasks", json={"title": "Low", "priority": "low"})
        resp = client.get("/api/tasks?priority=high")
        assert len(resp.json()) == 1
        assert resp.json()[0]["priority"] == "high"

    def test_sort_by_priority_asc(self, client):
        client.post("/api/tasks", json={"title": "High task", "priority": "high"})
        client.post("/api/tasks", json={"title": "Low task", "priority": "low"})
        client.post("/api/tasks", json={"title": "Medium task", "priority": "medium"})
        resp = client.get("/api/tasks?sort_by=priority&sort_order=asc")
        assert resp.status_code == 200
        priorities = [t["priority"] for t in resp.json()]
        assert priorities == ["low", "medium", "high"]

    def test_sort_by_priority_desc(self, client):
        client.post("/api/tasks", json={"title": "Low task", "priority": "low"})
        client.post("/api/tasks", json={"title": "High task", "priority": "high"})
        client.post("/api/tasks", json={"title": "Medium task", "priority": "medium"})
        resp = client.get("/api/tasks?sort_by=priority&sort_order=desc")
        assert resp.status_code == 200
        priorities = [t["priority"] for t in resp.json()]
        assert priorities == ["high", "medium", "low"]

    def test_sort_by_created_at_asc(self, client):
        client.post("/api/tasks", json={"title": "First"})
        client.post("/api/tasks", json={"title": "Second"})
        resp = client.get("/api/tasks?sort_by=created_at&sort_order=asc")
        assert resp.status_code == 200
        titles = [t["title"] for t in resp.json()]
        assert titles[0] == "First"
        assert titles[1] == "Second"

    def test_sort_by_created_at_desc(self, client):
        client.post("/api/tasks", json={"title": "First"})
        client.post("/api/tasks", json={"title": "Second"})
        resp = client.get("/api/tasks?sort_by=created_at&sort_order=desc")
        assert resp.status_code == 200
        titles = [t["title"] for t in resp.json()]
        assert titles[0] == "Second"
        assert titles[1] == "First"

    def test_sort_by_title(self, client):
        client.post("/api/tasks", json={"title": "Charlie"})
        client.post("/api/tasks", json={"title": "Alpha"})
        client.post("/api/tasks", json={"title": "Bravo"})
        resp = client.get("/api/tasks?sort_by=title&sort_order=asc")
        assert resp.status_code == 200
        titles = [t["title"] for t in resp.json()]
        assert titles == ["Alpha", "Bravo", "Charlie"]

    def test_invalid_sort_by_returns_400(self, client):
        resp = client.get("/api/tasks?sort_by=invalid")
        assert resp.status_code == 400

    def test_invalid_sort_order_returns_400(self, client):
        resp = client.get("/api/tasks?sort_order=invalid")
        assert resp.status_code == 400

    def test_default_sort_is_created_at_desc(self, client):
        client.post("/api/tasks", json={"title": "First"})
        client.post("/api/tasks", json={"title": "Second"})
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        titles = [t["title"] for t in resp.json()]
        assert titles[0] == "Second"
        assert titles[1] == "First"


class TestGetTask:
    def test_get_task(self, client):
        created = client.post("/api/tasks", json={"title": "My task"}).json()
        resp = client.get(f"/api/tasks/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "My task"

    def test_get_task_not_found(self, client):
        resp = client.get("/api/tasks/9999")
        assert resp.status_code == 404


class TestUpdateTask:
    def test_update_title(self, client):
        created = client.post("/api/tasks", json={"title": "Old"}).json()
        resp = client.patch(f"/api/tasks/{created['id']}", json={"title": "New"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "New"

    def test_mark_complete(self, client):
        created = client.post("/api/tasks", json={"title": "Task"}).json()
        resp = client.patch(f"/api/tasks/{created['id']}", json={"completed": True})
        assert resp.json()["completed"] is True

    def test_update_not_found(self, client):
        resp = client.patch("/api/tasks/9999", json={"title": "X"})
        assert resp.status_code == 404

    def test_update_invalid_priority(self, client):
        created = client.post("/api/tasks", json={"title": "Task"}).json()
        resp = client.patch(f"/api/tasks/{created['id']}", json={"priority": "urgent"})
        assert resp.status_code == 400

    def test_update_valid_priority(self, client):
        created = client.post("/api/tasks", json={"title": "Task"}).json()
        resp = client.patch(f"/api/tasks/{created['id']}", json={"priority": "high"})
        assert resp.status_code == 200
        assert resp.json()["priority"] == "high"

    def test_update_without_priority(self, client):
        created = client.post("/api/tasks", json={"title": "Task", "priority": "low"}).json()
        resp = client.patch(f"/api/tasks/{created['id']}", json={"title": "X"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "X"
        assert resp.json()["priority"] == "low"


class TestDeleteTask:
    def test_delete_task(self, client):
        created = client.post("/api/tasks", json={"title": "To delete"}).json()
        resp = client.delete(f"/api/tasks/{created['id']}")
        assert resp.status_code == 204
        # Verify it's gone
        assert client.get(f"/api/tasks/{created['id']}").status_code == 404

    def test_delete_not_found(self, client):
        resp = client.delete("/api/tasks/9999")
        assert resp.status_code == 404


class TestSearch:
    def test_search_by_title(self, client):
        client.post("/api/tasks", json={"title": "Buy milk"})
        client.post("/api/tasks", json={"title": "Walk dog"})
        resp = client.get("/api/tasks/search?q=milk")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == "Buy milk"

    def test_search_by_description(self, client):
        client.post("/api/tasks", json={"title": "Task", "description": "Quarterly review"})
        resp = client.get("/api/tasks/search?q=Quarterly")
        assert len(resp.json()) == 1

    def test_search_no_results(self, client):
        client.post("/api/tasks", json={"title": "Something"})
        resp = client.get("/api/tasks/search?q=nonexistent")
        assert resp.json() == []

    def test_search_requires_query(self, client):
        resp = client.get("/api/tasks/search")
        assert resp.status_code == 422
