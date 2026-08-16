import os

import requests


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ApiClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = 15

    def _headers(self):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @staticmethod
    def _handle_response(resp):
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except ValueError:
                detail = resp.text or f"Error {resp.status_code}"
            raise ApiError(str(detail), resp.status_code)
        return resp

    def test_connection(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def register(self, username: str, password: str, nama_lengkap: str = "", register_code: str = ""):
        resp = requests.post(
            f"{self.base_url}/auth/register",
            json={
                "username": username,
                "password": password,
                "nama_lengkap": nama_lengkap or None,
                "register_code": register_code or None,
            },
            timeout=self.timeout,
        )
        self._handle_response(resp)
        return resp.json()

    def login(self, username: str, password: str):
        resp = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password},
            timeout=self.timeout,
        )
        self._handle_response(resp)
        return resp.json()

    def list_posters(self, category="all", search="", page=1, page_size=20):
        resp = requests.get(
            f"{self.base_url}/posters",
            params={"category": category, "search": search, "page": page, "page_size": page_size},
            headers=self._headers(),
            timeout=self.timeout,
        )
        self._handle_response(resp)
        return resp.json()

    def get_stats(self):
        resp = requests.get(f"{self.base_url}/posters/stats", headers=self._headers(), timeout=self.timeout)
        self._handle_response(resp)
        return resp.json()

    def get_thumbnail_bytes(self, poster_id: int) -> bytes:
        resp = requests.get(
            f"{self.base_url}/posters/{poster_id}/thumbnail", headers=self._headers(), timeout=self.timeout
        )
        self._handle_response(resp)
        return resp.content

    def get_file_bytes(self, poster_id: int) -> bytes:
        resp = requests.get(f"{self.base_url}/posters/{poster_id}/file", headers=self._headers(), timeout=30)
        self._handle_response(resp)
        return resp.content

    def upload_poster(self, filepath: str, tags: str = ""):
        with open(filepath, "rb") as f:
            files = {"file": (os.path.basename(filepath), f, self._guess_mime(filepath))}
            data = {"tags": tags}
            resp = requests.post(
                f"{self.base_url}/posters/upload",
                files=files,
                data=data,
                headers=self._headers(),
                timeout=60,
            )
        self._handle_response(resp)
        return resp.json()

    def delete_poster(self, poster_id: int):
        resp = requests.delete(
            f"{self.base_url}/posters/{poster_id}", headers=self._headers(), timeout=self.timeout
        )
        self._handle_response(resp)
        return resp.json()

    @staticmethod
    def _guess_mime(filepath: str) -> str:
        ext = filepath.lower().rsplit(".", 1)[-1]
        return {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext, "application/octet-stream")
