import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_department(client: AsyncClient):
    payload = {"name": "IT Department", "parent_id": None}
    response = await client.post("/departments/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "IT Department"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_department_duplicate_same_parent(client: AsyncClient):
    # Создаем первый отдел
    await client.post("/departments/", json={"name": "Backend"})
    # Пытаемся создать второй с таким же именем
    response = await client.post("/departments/", json={"name": "Backend"})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_department_empty_name(client: AsyncClient):
    response = await client.post("/departments/", json={"name": "   "})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_department_not_found(client: AsyncClient):
    response = await client.get("/departments/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_department_with_tree(client: AsyncClient):
    # Создаем корневой отдел
    root_resp = await client.post("/departments/", json={"name": "Root"})
    root_id = root_resp.json()["id"]
    # Создаем дочерний
    child_resp = await client.post("/departments/", json={"name": "Child", "parent_id": root_id})
    child_id = child_resp.json()["id"]
    # Создаем сотрудника в дочернем
    emp_payload = {"full_name": "John Doe", "position": "Developer"}
    await client.post(f"/departments/{child_id}/employees/", json=emp_payload)

    # Получаем дерево глубиной 2
    response = await client.get(f"/departments/{root_id}?depth=2&include_employees=true")
    assert response.status_code == 200
    data = response.json()
    assert data["department"]["name"] == "Root"
    assert len(data["children"]) == 1
    assert data["children"][0]["name"] == "Child"
    assert len(data["children"][0]["employees"]) == 1


@pytest.mark.asyncio
async def test_update_department_prevent_cycle(client: AsyncClient):
    # Создаем два отдела: A и B, где B дочерний A
    resp_a = await client.post("/departments/", json={"name": "A"})
    a_id = resp_a.json()["id"]
    resp_b = await client.post("/departments/", json={"name": "B", "parent_id": a_id})
    b_id = resp_b.json()["id"]
    # Пытаемся сделать A родителем B (уже есть), но пытаемся сделать B родителем A -> цикл
    response = await client.patch(f"/departments/{a_id}", json={"parent_id": b_id})
    assert response.status_code == 409
    assert "subtree" in response.json()["detail"]


async def test_update_department_duplicate_name(client: AsyncClient):
    # Создаем два отдела
    resp_a = await client.post("/departments/", json={"name": "A"})
    assert resp_a.status_code == 200

    resp_b = await client.post("/departments/", json={"name": "B"})
    assert resp_b.status_code == 200
    b_id = resp_b.json()["id"]

    # Пытаемся переименовать B в A (оба корневые)
    response = await client.patch(f"/departments/{b_id}", json={"name": "A"})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_department_cascade(client: AsyncClient):
    # Создаем отдел с сотрудником
    dept_resp = await client.post("/departments/", json={"name": "ToDelete"})
    dept_id = dept_resp.json()["id"]
    emp_payload = {"full_name": "Jane", "position": "Manager"}
    await client.post(f"/departments/{dept_id}/employees/", json=emp_payload)

    # Удаляем каскадно
    response = await client.delete(f"/departments/{dept_id}?mode=cascade")
    assert response.status_code == 200

    # Проверяем, что отдел удален
    get_resp = await client.get(f"/departments/{dept_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_department_reassign(client: AsyncClient):
    # Создаем два отдела: исходный и целевой
    src_resp = await client.post("/departments/", json={"name": "Source"})
    src_id = src_resp.json()["id"]
    tgt_resp = await client.post("/departments/", json={"name": "Target"})
    tgt_id = tgt_resp.json()["id"]

    # Создаем сотрудника в исходном
    emp_payload = {"full_name": "Bob", "position": "Dev"}
    await client.post(f"/departments/{src_id}/employees/", json=emp_payload)

    # Удаляем с переводом
    response = await client.delete(f"/departments/{src_id}?mode=reassign&reassign_to_department_id={tgt_id}")
    assert response.status_code == 200

    # Проверяем, что исходный отдел удален
    get_resp = await client.get(f"/departments/{src_id}")
    assert get_resp.status_code == 404
