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


class TestTags:
    def test_create_task_with_tags(self, client):
        resp = client.post(
            "/api/tasks",
            json={"title": "Tagged task", "tags": ["urgent", "backend"]},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert isinstance(data["tags"], list)
        assert set(data["tags"]) == {"urgent", "backend"}
        # All tag names should be lowercased
        for name in data["tags"]:
            assert name == name.lower()

    def test_create_task_without_tags_defaults_empty(self, client):
        resp = client.post("/api/tasks", json={"title": "No tags"})
        assert resp.status_code == 201
        assert resp.json()["tags"] == []

    def test_tags_are_normalized(self, client):
        resp = client.post(
            "/api/tasks",
            json={"title": "Normalize me", "tags": ["Urgent", " Backend "]},
        )
        assert resp.status_code == 201
        assert set(resp.json()["tags"]) == {"urgent", "backend"}

    def test_duplicate_tags_deduped(self, client):
        resp = client.post(
            "/api/tasks",
            json={"title": "Dupes", "tags": ["urgent", "Urgent", "URGENT", " urgent "]},
        )
        assert resp.status_code == 201
        assert resp.json()["tags"] == ["urgent"]

    def test_get_task_includes_tags(self, client):
        created = client.post(
            "/api/tasks",
            json={"title": "Has tags", "tags": ["alpha", "beta"]},
        ).json()
        resp = client.get(f"/api/tasks/{created['id']}")
        assert resp.status_code == 200
        assert set(resp.json()["tags"]) == {"alpha", "beta"}

    def test_patch_set_tags(self, client):
        created = client.post("/api/tasks", json={"title": "Task"}).json()
        resp = client.patch(
            f"/api/tasks/{created['id']}",
            json={"tags": ["x", "y"]},
        )
        assert resp.status_code == 200
        assert set(resp.json()["tags"]) == {"x", "y"}

    def test_patch_replace_tags(self, client):
        created = client.post(
            "/api/tasks",
            json={"title": "Task", "tags": ["old"]},
        ).json()
        resp = client.patch(
            f"/api/tasks/{created['id']}",
            json={"tags": ["new"]},
        )
        assert resp.status_code == 200
        assert resp.json()["tags"] == ["new"]

    def test_patch_clear_tags_with_empty_list(self, client):
        created = client.post(
            "/api/tasks",
            json={"title": "Task", "tags": ["a", "b"]},
        ).json()
        resp = client.patch(
            f"/api/tasks/{created['id']}",
            json={"tags": []},
        )
        assert resp.status_code == 200
        assert resp.json()["tags"] == []

    def test_patch_without_tags_key_leaves_tags_unchanged(self, client):
        created = client.post(
            "/api/tasks",
            json={"title": "Task", "tags": ["keep"]},
        ).json()
        resp = client.patch(
            f"/api/tasks/{created['id']}",
            json={"title": "Renamed"},
        )
        assert resp.status_code == 200
        assert resp.json()["tags"] == ["keep"]

    def test_filter_by_tag(self, client):
        client.post("/api/tasks", json={"title": "Urgent one", "tags": ["urgent"]})
        client.post("/api/tasks", json={"title": "Normal one", "tags": ["normal"]})
        resp = client.get("/api/tasks?tag=urgent")
        assert resp.status_code == 200
        tasks = resp.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Urgent one"

    def test_filter_by_nonexistent_tag_returns_empty(self, client):
        client.post("/api/tasks", json={"title": "Task", "tags": ["real"]})
        resp = client.get("/api/tasks?tag=nonexistent")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_tag_filter_combines_with_completed(self, client):
        client.post("/api/tasks", json={"title": "Done urgent", "tags": ["urgent"]})
        client.post("/api/tasks", json={"title": "Open urgent", "tags": ["urgent"]})
        client.post("/api/tasks", json={"title": "Open normal", "tags": ["normal"]})
        # Complete the first task
        tasks = client.get("/api/tasks?tag=urgent").json()
        done_task = [t for t in tasks if t["title"] == "Done urgent"][0]
        client.patch(f"/api/tasks/{done_task['id']}", json={"completed": True})

        resp = client.get("/api/tasks?tag=urgent&completed=true")
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == "Done urgent"

        resp = client.get("/api/tasks?tag=urgent&completed=false")
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == "Open urgent"

    def test_tag_filter_combines_with_priority(self, client):
        client.post(
            "/api/tasks",
            json={"title": "High urgent", "priority": "high", "tags": ["urgent"]},
        )
        client.post(
            "/api/tasks",
            json={"title": "Low urgent", "priority": "low", "tags": ["urgent"]},
        )
        client.post(
            "/api/tasks",
            json={"title": "High normal", "priority": "high", "tags": ["normal"]},
        )
        resp = client.get("/api/tasks?tag=urgent&priority=high")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == "High urgent"

    def test_search_matches_tag_name(self, client):
        client.post("/api/tasks", json={"title": "Some task", "tags": ["backend"]})
        client.post("/api/tasks", json={"title": "Another", "tags": ["frontend"]})
        resp = client.get("/api/tasks/search?q=backend")
        assert resp.status_code == 200
        tasks = resp.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Some task"

    def test_list_all_tags_sorted(self, client):
        client.post("/api/tasks", json={"title": "T1", "tags": ["zebra", "apple"]})
        client.post("/api/tasks", json={"title": "T2", "tags": ["mango", "apple"]})
        resp = client.get("/api/tags")
        assert resp.status_code == 200
        tags = resp.json()
        names = [t["name"] for t in tags]
        assert names == sorted(names)
        assert set(names) == {"zebra", "apple", "mango"}

    def test_delete_task_removes_it(self, client):
        created = client.post(
            "/api/tasks",
            json={"title": "To delete", "tags": ["temp"]},
        ).json()
        resp = client.delete(f"/api/tasks/{created['id']}")
        assert resp.status_code == 204
        assert client.get(f"/api/tasks/{created['id']}").status_code == 404
