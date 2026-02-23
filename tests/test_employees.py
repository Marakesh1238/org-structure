import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_employee(client: AsyncClient):
    # Сначала создаем отдел
    dept_resp = await client.post("/departments/", json={"name": "IT"})
    dept_id = dept_resp.json()["id"]

    payload = {
        "full_name": "Иван Петров",
        "position": "Разработчик",
        "hired_at": "2023-01-15"
    }
    response = await client.post(f"/departments/{dept_id}/employees/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Иван Петров"
    assert data["department_id"] == dept_id
    assert data["hired_at"] == "2023-01-15"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_employee_department_not_found(client: AsyncClient):
    payload = {"full_name": "Иван", "position": "Dev"}
    response = await client.post("/departments/999/employees/", json=payload)
    assert response.status_code == 404
    assert "Department not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_employee_trimming(client: AsyncClient):
    dept_resp = await client.post("/departments/", json={"name": "HR"})
    dept_id = dept_resp.json()["id"]

    payload = {
        "full_name": "  Анна Сергеева  ",
        "position": "  Менеджер  "
    }
    response = await client.post(f"/departments/{dept_id}/employees/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Анна Сергеева"
    assert data["position"] == "Менеджер"


@pytest.mark.asyncio
async def test_create_employee_empty_name(client: AsyncClient):
    dept_resp = await client.post("/departments/", json={"name": "HR"})
    dept_id = dept_resp.json()["id"]

    payload = {"full_name": "", "position": "Dev"}
    response = await client.post(f"/departments/{dept_id}/employees/", json=payload)
    assert response.status_code == 422