from database import Database

database = Database()


def format_groups_with_users(user_id: int) -> str:
    """
    Formats the list of groups and their members for a given user into a readable string.
    """

    user_groups = database.get_user_groups(user_id)
    return "\n\n".join(
        f"Группа: {group.name}\nУчастники: {', '.join(user.name for user in database.get_group_users(group.id))}"
        for group in user_groups
    )
