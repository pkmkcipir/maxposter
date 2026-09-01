from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from . import database, models, config
from .routers import auth_router, poster_router, folder_router
from .search import setup_fts

models.Base.metadata.create_all(bind=database.engine)
database.run_migrations()
setup_fts()

app = FastAPI(title="Maxposter Server", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(folder_router.router)
app.include_router(poster_router.router)


@app.get("/")
def root():
    """Menyajikan aplikasi web Maxposter -- ini yang membuat server bisa
    diakses langsung lewat browser dengan memasukkan alamat IP-nya."""
    return FileResponse(config.WEB_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "healthy"}
