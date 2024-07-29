from fastapi import FastAPI
from jose import jwt


class IntegratedServices:
    def __init__(
        self,
        workbench_service_app: FastAPI,
        canonical_assistant_service_app: FastAPI,
    ):
        self.workbench_service_app = workbench_service_app
        self.canonical_assistant_service_app = canonical_assistant_service_app


class MockUser:
    tenant_id: str
    object_id: str
    name: str

    app_id: str = "test-app-id"
    token_algo: str = "HS256"

    def __init__(self, tenant_id: str, object_id: str, name: str):
        self.tenant_id = tenant_id
        self.object_id = object_id
        self.name = name

    @property
    def id(self) -> str:
        return f"{self.tenant_id}.{self.object_id}"

    @property
    def jwt_token(self) -> str:
        return jwt.encode(
            claims={
                "tid": self.tenant_id,
                "oid": self.object_id,
                "name": self.name,
                "appid": self.app_id,
            },
            key="",
            algorithm=self.token_algo,
        )

    @property
    def authorization_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.jwt_token}"}
