import datetime
from sqlalchemy import create_engine, Table, Column, Integer, DateTime, MetaData, ForeignKey, inspect, select, update, insert
from models import GroupAndStatusModel


class DBException(Exception):
    pass


class Database():

    def __init__(self, user, password, database, port, host):
        self.database_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
        self.engine = create_engine(self.database_uri)

        self.meta = MetaData()

        self.vk_user_ids = Table(
            "vk_user_ids",
            self.meta,
            Column("id", Integer, primary_key=True, nullable=False),
            Column("vk_user_id", Integer, nullable=False),
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

        self.id_group_link = Table(
            "id_group_link",
            self.meta,
            Column("vk_user_id", Integer, ForeignKey(
                "vk_user_ids.id"), nullable=False),
            Column("group_id", Integer, ForeignKey(
                "vk_groups.id"), nullable=False),
        )

    def tables_exist(self):
        try:
            if (not inspect(self.engine).has_table("vk_user_ids")) or (not inspect(self.engine).has_table("vk_groups")) or (not inspect(self.engine).has_table("id_group_link")):
                return False
            return True
        except Exception as exc:
            raise DBException(f"Error in tables_exist: {exc}") from exc

    def migrate(self):
        try:
            self.meta.create_all(self.engine)
        except Exception as exc:
            raise DBException(f"Error in migrate: {exc}") from exc

    def add_user_id(self, vk_user_id):
        try:
            with self.engine.connect() as connection:
                insert_query = insert(self.vk_user_ids).values(
                    vk_user_id=vk_user_id)
                connection.execute(insert_query)
        except Exception as exc:
            raise DBException(f"Error in add_user_id: {exc}") from exc

    def is_valid_user_id(self, vk_user_id):
        try:
            with self.engine.connect() as connection:
                select_query = select(self.vk_user_ids).where(
                    self.vk_user_ids.c.vk_user_id == vk_user_id)
                result = connection.execute(select_query).fetchall()
                if len(result) == 0:
                    return False
                return True
        except Exception as exc:
            raise DBException(f"Error in is_valid_user_id: {exc}") from exc

    def add_group(self, group_id, vk_user_id):
        try:
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

                select_vk_user_id_query = select(self.vk_user_ids.c.id).where(
                    self.vk_user_ids.c.vk_user_id == vk_user_id)
                vk_user_id_link = connection.execute(
                    select_vk_user_id_query).fetchall()[0][0]

                insert_link_query = insert(self.id_group_link).values(
                    group_id=group_id_link, vk_user_id=vk_user_id_link)
                connection.execute(insert_link_query)
        except Exception as exc:
            raise DBException(f"Error in add_group: {exc}") from exc

    def update_group_status(self, group_id, status):
        try:
            with self.engine.connect() as connection:
                update_query = update(self.vk_groups).where(
                    self.vk_groups.c.group_id == group_id).values(status_id=status)
                connection.execute(update_query)
        except Exception as exc:
            raise DBException(f"Error in update_group_status: {exc}") from exc

    def get_group_status(self, group_id):
        try:
            with self.engine.connect() as connection:
                select_query = select(self.vk_groups).where(
                    self.vk_groups.c.group_id == group_id)
                result = connection.execute(select_query).fetchall()
                if len(result) == 0:
                    return 2  # GROUP NOT IN DATABASE
                status = result[0][2]
                return status
        except Exception as exc:
            raise DBException(f"Error in get_group_status: {exc}") from exc

    def get_all_groups(self):
        try:
            with self.engine.connect() as connection:
                select_query = select(self.vk_groups)
                result = connection.execute(select_query).fetchall()
                groups = [GroupAndStatusModel(
                    group_id=row[1], group_status=row[2]) for row in result]
                return groups
        except Exception as exc:
            raise DBException(f"Error in get_all_groups: {exc}") from exc

    def get_owned_groups(self, vk_user_id):
        try:
            with self.engine.connect() as connection:
                select_vk_user_id_query = select(self.vk_user_ids.c.id).where(
                    self.vk_user_ids.c.vk_user_id == vk_user_id)
                vk_user_id_link = connection.execute(
                    select_vk_user_id_query).fetchall()[0][0]

                select_group_ids_query = select(self.id_group_link.c.group_id).where(
                    self.id_group_link.c.vk_user_id == vk_user_id_link)
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
            raise DBException(f"Error in get_owned_groups: {exc}") from exc
