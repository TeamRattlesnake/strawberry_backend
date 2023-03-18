import datetime
from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, MetaData, ForeignKey, inspect, select, delete, update, insert
from utils import make_sha256
from models import GroupAndStatusModel


class DBException(Exception):
    pass


class Database():

    def __init__(self, user, password, database, port, host):
        self.database_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
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
            Column("status_id", Integer, nullable=False),
            # 0:ready, 1:not_ready
        )

        self.token_group_link = Table(
            "token_group_link",
            self.meta,
            Column("token_id", Integer, ForeignKey(
                "vk_token_hashes.id"), nullable=False),
            Column("group_id", Integer, ForeignKey(
                "vk_groups.id"), nullable=False),
        )

    def tables_exist(self):
        try:
            if (not inspect(self.engine).has_table("vk_token_hashes")) or (not inspect(self.engine).has_table("vk_groups")) or (not inspect(self.engine).has_table("token_group_link")):
                return False
            return True
        except Exception as exc:
            raise DBException("Error in tables_exist") from exc

    def migrate(self):
        try:
            self.meta.create_all(self.engine)
        except Exception as exc:
            raise DBException("Error in migrate") from exc

    def add_token(self, vk_token):
        try:
            vk_token_hash = make_sha256(vk_token)
            with self.engine.connect() as connection:
                insert_query = insert(self.vk_token_hashes).values(
                    vk_token_hash=vk_token_hash)
                connection.execute(insert_query)
        except Exception as exc:
            raise DBException("Error in add_token") from exc

    def autoremove_old_tokens(self):
        try:
            too_old = datetime.datetime.today() - datetime.timedelta(days=1)
            with self.engine.connect() as connection:
                delete_query = delete(self.vk_token_hashes).where(
                    self.vk_token_hashes.c.acquired <= too_old)
                connection.execute(delete_query)
        except Exception as exc:
            raise DBException("Error in autoremove_old_tokens") from exc

    def is_valid_token(self, vk_token):
        try:
            vk_token_hash = make_sha256(vk_token)
            with self.engine.connect() as connection:
                select_query = select(self.vk_token_hashes).where(
                    self.vk_token_hashes.c.vk_token_hash == vk_token_hash)
                result = connection.execute(select_query).fetchall()
                if len(result) == 0:
                    return False
                return True
        except Exception as exc:
            raise DBException("Error in is_valid_token") from exc

    def update_token(self, old_vk_token, new_vk_token):
        try:
            old_vk_token_hash = make_sha256(old_vk_token)
            new_vk_token_hash = make_sha256(new_vk_token)
            with self.engine.connect() as connection:
                update_query = update(self.vk_token_hashes).where(
                    self.vk_token_hashes.c.vk_token_hash == old_vk_token_hash).values(vk_token_hash=new_vk_token_hash)
                connection.execute(update_query)
        except Exception as exc:
            raise DBException("Error in update_token") from exc

    def add_group(self, group_id, vk_token):
        try:
            vk_token_hash = make_sha256(vk_token)
            with self.engine.connect() as connection:

                select_group_count_query = select(self.vk_groups.c.id).where(
                    self.vk_groups.c.group_id == group_id)
                count = len(connection.execute(
                    select_group_count_query).fetchall())

                if count == 0:
                    insert_group_query = insert(self.vk_groups).values(
                        group_id=group_id, status_id=1)
                    connection.execute(insert_group_query)

                select_group_id_query = select(self.vk_groups.c.id).where(
                    self.vk_groups.c.group_id == group_id)
                group_id_link = connection.execute(
                    select_group_id_query).fetchall()[0][0]

                select_token_id_query = select(self.vk_token_hashes.c.id).where(
                    self.vk_token_hashes.c.vk_token_hash == vk_token_hash)
                token_id_link = connection.execute(
                    select_token_id_query).fetchall()[0][0]

                insert_link_query = insert(self.token_group_link).values(
                    group_id=group_id_link, token_id=token_id_link)
                connection.execute(insert_link_query)
        except Exception as exc:
            raise DBException("Error in add_group") from exc

    def update_group_status(self, group_id, status):
        try:
            with self.engine.connect() as connection:
                update_query = update(self.vk_groups).where(
                    self.vk_groups.c.group_id == group_id).values(status_id=status)
                connection.execute(update_query)
        except Exception as exc:
            raise DBException("Error in update_group_status") from exc

    def get_group_status(self, group_id):
        try:
            with self.engine.connect() as connection:
                select_query = select(self.vk_groups).where(
                    self.vk_groups.c.group_id == group_id)
                result = connection.execute(select_query).fetchall()
                status = result[0][2]
                return status
        except Exception as exc:
            raise DBException("Error in get_group_status") from exc

    def get_all_groups(self):
        try:
            with self.engine.connect() as connection:
                select_query = select(self.vk_groups)
                result = connection.execute(select_query).fetchall()
                groups = [GroupAndStatusModel(
                    group_id=row[1], group_status=row[2]) for row in result]
                return groups
        except Exception as exc:
            raise DBException("Error in get_all_groups") from exc

    def get_owned_groups(self, vk_token):
        try:
            vk_token_hash = make_sha256(vk_token)
            with self.engine.connect() as connection:
                select_token_id_query = select(self.vk_token_hashes.c.id).where(
                    self.vk_token_hashes.c.vk_token_hash == vk_token_hash)
                token_id_link = connection.execute(
                    select_token_id_query).fetchall()[0][0]

                select_group_ids_query = select(self.token_group_link.c.group_id).where(
                    self.token_group_link.c.token_id == token_id_link)
                select_group_ids = connection.execute(
                    select_group_ids_query).fetchall()
                select_group_ids = [row[0] for row in select_group_ids]

                select_query = select(self.vk_groups).where(
                    self.vk_groups.c.id.in_(select_group_ids))
                result = connection.execute(select_query).fetchall()

                groups = [GroupAndStatusModel(
                    group_id=row[1], group_status=row[2]) for row in result]
                return groups
        except Exception as exc:
            raise DBException("Error in get_owned_groups") from exc
