import discord

cleaned_up_perm = {
    "view_channels": "View Channels",
    "manage_channels": "Manage Channels",
    "manage_roles": "Manage Roles",
    "create_expressions": "Create Expressions",
    "manage_expressions": "Manage Expressions",
    "view_audit_log": "View Audit Log",
    "view_guild_insights": "View Server Insights",
    "manage_webhooks": "Manage Webhooks",
    "manage_guild": "Manage Server",
    "create_instant_invite": "Create Invite",
    "change_nickname": "Change Nickname",
    "manage_nicknames": "Manage Nicknames",
    "kick_members": "Kick Members",
    "ban_members": "Ban Members",
    "moderate_members": "Timeout Members",
    "send_messages": "Send Messages",
    "send_messages_in_threads": "Send Messages in Threads",
    "create_public_threads": "Create Public Threads",
    "create_private_threads": "Create Private Threads",
    "embed_links": "Embed Links",
    "attach_files": "Attach Files",
    "add_reactions": "Add Reactions",
    "external_emojis": "Use External Emoji",
    "external_stickers": "Use External Stickers",
    "mention_everyone": "Mention @everyone, @here, and All Roles",
    "manage_messages": "Manage Messages",
    "manage_threads": "Manage Threads",
    "read_message_history": "Read Message History",
    "send_tts_messages": "Send Text-to-Speech Messages",
    "send_voice_messages": "Send Voice Messages",
    "create_polls": "Create Polls",
    "connect": "Connect",
    "speak": "Speak",
    "stream": "Video",
    "use_soundboard": "Use Soundboard",
    "use_external_sounds": "Use External Sounds",
    "use_voice_activation": "Use Voice Activity",
    "priority_speaker": "Priority Speaker",
    "mute_members": "Mute Members",
    "deafen_members": "Deafen Members",
    "move_members": "Move Members",
    "vcstatus": "Set Voice Channel Status",
    "use_application_commands": "Use Application Commands",
    "use_embedded_activities": "Use Activities",
    "use_external_apps": "Use External Apps",
    "request_to_speak": "Request to Speak",
    "create_events": "Create Events",
    "manage_events": "Manage Events",
    "administrator": "Administrator",
    "read_messages": "View Channel",
    "manage_permissions": "Manage Permissions",
}

async def channel_role_overrides(overwrite: discord.PermissionOverwrite):
    """Grabs the list of overwrites and determines which permissions are allowed and denied, and returns the cleaned up version of those permissions"""
    allowed_perms = []
    denied_perms = []
    if not overwrite.is_empty():
        allow, deny = overwrite.pair()
        for perm, value in iter(allow):
            if value:
                perm_s = cleaned_up_perm.get(perm, "DEFAULT")
                if perm_s == "DEFAULT":
                    print(perm)
                allowed_perms.append(perm_s)
        for perm, value in iter(deny):
            if value:
                perm_s = cleaned_up_perm.get(perm, "DEFAULT")
                if perm_s == "DEFAULT":
                    print(perm)
                denied_perms.append(perm_s)
    return allowed_perms, denied_perms

async def role_permissions(role: discord.Role):
    """Grabs the list of permissions that a role has, and returns a list with the cleaned up version of those permissions"""
    permissions_list = []
    for perm, value in iter(role.permissions):
        if value:
            permissions_list.append(cleaned_up_perm.get(perm, perm).lower())
    return permissions_list