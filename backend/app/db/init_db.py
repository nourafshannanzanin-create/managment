from sqlalchemy import delete, select, text

from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import User
from app.seed import seed_database


def reset_seed_data() -> None:
    with SessionLocal() as session:
        session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(delete(table))
        session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        session.commit()


def initialize_database(seed: bool = True) -> None:
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    if not seed:
        return

    with SessionLocal() as session:
        has_users = session.scalar(select(User.id).limit(1)) is not None
        if not has_users:
            reset_seed_data()
            seed_database(session)
