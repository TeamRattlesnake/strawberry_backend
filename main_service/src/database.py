import datetime
from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, MetaData, inspect, select, delete, update, insert
from utils import make_sha256
from models import GroupAndStatusModel


class Database():

    def __init__(self, user, password, database, port, host):
        self.database_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
        print(self.database_uri)
        self.engine = create_engine(self.database_uri)

        self.meta = MetaData()

        self.vk_token_hashes = Table(
            "vk_token_hashes",
            self.meta,
            Column("id", Integer, primary_key=True, nullable=False),
            Column("vk_token_hash", String(256), nullable=False),
            Column("acquired", DateTime(timezone=True),
                   default=datetime.datetime.utcnow, nullable=False),
        )

        self.vk_groups = Table(
            "vk_groups",
            self.meta,
            Column("id", Integer, primary_key=True, nullable=False),
            Column("group_id", Integer, nullable=False),
            # 0:ready, 1:not_ready
            Column("status_id", Integer, nullable=False),
        )

    def tables_exist(self):
        if (not inspect(self.engine).has_table("vk_token_hashes")) or (not inspect(self.engine).has_table("vk_groups")):
            return False
        return True

    def migrate(self):
        self.meta.create_all(self.engine)

    def add_token(self, vk_token):
        vk_token_hash = make_sha256(vk_token)
        with self.engine.connect() as connection:
            insert_query = insert(self.vk_token_hashes).values(
                vk_token_hash=vk_token_hash)
            connection.execute(insert_query)

    def autoremove_old_tokens(self):
        too_old = datetime.datetime.today() - datetime.timedelta(days=1)
        with self.engine.connect() as connection:
            delete_query = delete(self.vk_token_hashes).where(
                self.vk_token_hashes.c.acquired <= too_old)
            connection.execute(delete_query)

    def is_valid_token(self, vk_token):
        return True
        vk_token_hash = make_sha256(vk_token)
        with self.engine.connect() as connection:
            select_query = select(self.vk_token_hashes).where(
                self.vk_token_hashes.c.vk_token_hash == vk_token_hash)
            result = connection.execute(select_query).fetchall()
            if len(result) == 0:
                return False
            return True

    def add_group(self, group_id):
        with self.engine.connect() as connection:
            insert_query = insert(self.vk_groups).values(
                group_id=group_id, status_id=1)
            connection.execute(insert_query)

    def update_group_status(self, group_id, status):
        with self.engine.connect() as connection:
            update_query = update(self.vk_groups).where(
                self.vk_groups.c.group_id == group_id).values(status_id=status)
            connection.execute(update_query)

    def get_group_status(self, group_id):
        with self.engine.connect() as connection:
            select_query = select(self.vk_groups).where(
                self.vk_groups.c.group_id == group_id)
            result = connection.execute(select_query).fetchall()
            status = result[0][2]
            return status

    def get_all_groups(self):
        with self.engine.connect() as connection:
            select_query = select(self.vk_groups)
            result = connection.execute(select_query).fetchall()
            groups = [GroupAndStatusModel(
                group_id=row[1], group_status=row[2]) for row in result]
            return groups
