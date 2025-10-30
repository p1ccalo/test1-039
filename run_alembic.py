from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
import os
import dotenv

dotenv.load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def run_alembic():
    engine = create_engine(DATABASE_URL)
    session = sessionmaker(bind=engine)
    alembic_cfg = Config('alembic.ini')
    alembic_cfg.set_main_option('script_location', 'alembic/versions')
    alembic_cfg.set_main_option('sqlalchemy_url', DATABASE_URL)
    command.upgrade(alembic_cfg, 'head')

if __name__ == '__main__':
    run_alembic()