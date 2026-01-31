from discord import app_commands

from .schedule_delete import register as register_schedule_delete
from .schedule_fix import register as register_schedule_fix
from .schedule_info import register as register_schedule_info
from .schedule_list import register as register_schedule_list


def setup_schedule_commands(tree: app_commands.CommandTree, db, upcoming_category_id: int, ended_category_id: int) -> None:
    schedule_group = app_commands.Group(name='schedule', description='スケジュール管理コマンド')

    register_schedule_list(schedule_group, db)
    register_schedule_info(schedule_group, db)
    register_schedule_delete(schedule_group, db)
    register_schedule_fix(schedule_group, db, upcoming_category_id, ended_category_id)

    tree.add_command(schedule_group)
