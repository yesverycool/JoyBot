import os

import discord
from discord.ext import commands

from datetime import datetime

# import lots of shit
from data import add_channel, add_tag_alias_db, remove_tag_alias_db, add_group_alias_db, remove_group_alias_db, \
    add_cont_from_one_user_to_other, perma_user_db, remove_perma_user_db, delete_link_from_database
from data import remove_member_alias_db, add_member_alias_db, add_tag, find_group_id, add_group, remove_group
from data import remove_moderator, add_moderator, get_members_of_group, add_member, remove_member, apis_dict
from data import remove_auditing_channel, add_auditing_channel, remove_command, remove_link, remove_tag_from_link
from data import remove_tag, check_user_is_mod, check_user_is_owner

from embeds import success_embed, error_embed, permission_denied_embed


def is_owner():
    def check_owner(ctx):
        x = check_user_is_owner(ctx)
        return True if x else False
    return commands.check(check_owner)


def is_mod():
    async def check_mod(ctx):
        x = check_user_is_mod(ctx)
        return True if x else False
    return commands.check(check_mod)


class Owner(commands.Cog):
    """Commands for the owner.
    """
    def __init__(self, disclient):
        """Initialise client."""
        self.disclient = disclient

    @commands.command(name='muc', aliases=['merge_user_cont', 'mergeusercont'])
    @is_owner()
    async def merge_user_contribution(self, ctx, member1: discord.Member, member2: discord.Member):
        """Add contribution from first arguement to second argument"""
        add_cont_from_one_user_to_other(member1.id, member2.id)
        ctx.send(embed=success_embed('Merged user contribution'))

    @commands.command(name='forcedelete', aliases=['forcedel', 'fdel'])
    @is_owner()
    async def force_delete_link(self, ctx, *links):
        delcounter = 0
        for link in links:
            removed = delete_link_from_database(link)
            if removed:
                delcounter += 1
            else:
                await ctx.send(f'failed to removed {link}')
        if delcounter > 0:
            await ctx.send(embed=success_embed(f'Removed {delcounter} link(s)!'))

    @commands.command()
    @is_owner()
    async def remove_moderator(self, ctx, member: discord.Member):
        """Add user to moderator list."""
        removed = remove_moderator(member.id)
        if removed:
            await ctx.send(embed=success_embed(f'{member} is no longer a moderator!'))
        else:
            await ctx.send(embed=error_embed(f'{member} is not a moderator!'))

    @commands.command()
    @is_owner()
    async def add_moderator(self, ctx, member: discord.Member):
        """Add user to moderator list."""
        added = add_moderator(member.id)
        if added:
            await ctx.send(embed=success_embed(f'{member} is now a moderator!'))
        else:
            await ctx.send(embed=error_embed(f'{member} is already a moderator!'))

    @commands.command()
    @is_owner()
    async def reload(self, ctx, cog_name=None):
        """Reload cog."""
        embed = discord.Embed(title='Reloading Results',
                              description='\uFEFF',
                              color=discord.Color.blurple())
        if cog_name is None:
            async with ctx.typing():
                reloaded = []
                failed = []
                for cog in os.listdir("./cogs"):
                    if cog.endswith(".py"):
                        try:
                            cog = f"cogs.{cog.replace('.py', '')}"
                            self.disclient.unload_extension(cog)
                            self.disclient.load_extension(cog)
                            reloaded.append(str(cog[5:]))
                        except commands.ExtensionNotLoaded:
                            failed.append(str(cog[5:]))
                if reloaded:
                    embed.add_field(name="Reloaded:",
                                    value=', '.join(reloaded))
                if failed:
                    embed.add_field(name="Failed to load:",
                                    value=', '.join(failed))
        else:
            async with ctx.typing():
                reloaded = []
                failed = []
                for cog in os.listdir("./cogs"):
                    if cog.endswith('.py'):
                        if cog[:-3] == cog_name:
                            cog = f"cogs.{cog.replace('.py', '')}"
                            try:
                                self.disclient.unload_extension(cog)
                                self.disclient.load_extension(cog)
                                reloaded.append(str(cog[5:]))
                            except commands.ExtensionNotLoaded:
                                failed.append(str(cog[5:]))
                if reloaded:
                    embed.add_field(name=f"Reloaded:",
                                    value=', '.join(reloaded))
                if failed:
                    embed.add_field(name=f"Failed to load:",
                                    value=', '.join(failed))
        await ctx.send(embed=embed)

    @commands.command()
    @is_owner()
    async def unload(self, ctx, cog_name):
        for cog in os.listdir("./cogs"):
            if cog.endswith(".py"):
                if cog[:-3] == cog_name:
                    cog = f"cogs.{cog.replace('.py', '')}"
                    try:
                        self.disclient.unload_extension(cog)
                    except commands.ExtensionNotLoaded:
                        await ctx.send('Failed to unload cog.')
        await ctx.send('Unloaded cog!')

    @commands.command()
    @is_owner()
    async def load(self, ctx, cog_name):
        for cog in os.listdir("./cogs"):
            if cog.endswith(".py"):
                if cog[:-3] == cog_name:
                    cog = f"cogs.{cog.replace('.py', '')}"
                    try:
                        self.disclient.load_extension(cog)
                    except commands.ExtensionNotLoaded:
                        await ctx.send('Failed to load cog.')
        await ctx.send('Loaded cog!')

    @commands.command()
    @is_owner()
    async def perma_user(self, ctx, user_id):
        """Stops user from added anything to the bot"""
        perma = perma_user_db(user_id)
        if perma:
            await ctx.send(embed=success_embed("User successfully perma'd."))
        else:
            await ctx.send(embed=error_embed("Failed to perma user."))

    @commands.command()
    @is_owner()
    async def remove_perma_user(self, ctx, user_id):
        """Removes user from perma ban"""
        unperma = remove_perma_user_db(user_id)
        if unperma:
            await ctx.send(embed=success_embed("User un-perma'd."))
        else:
            await ctx.send(embed=error_embed("Failed to un-perma user."))


class Moderation(commands.Cog):
    """Commands for Joy moderators.
    """
    def __init__(self, disclient):
        """Initialise client."""
        self.disclient = disclient

    @commands.command(aliases=['addgroups', 'addgroup', 'add_groups'])
    @is_mod()
    async def add_group(self, ctx, *args):
        """Adds a group or list of groups"""
        group_list = args
        if not group_list:
            await ctx.send(embed=error_embed('No group(s) given!'))
        else:
            # Update to string instead of list
            already_exists = []
            added = []
            for group in group_list:
                groupstr = str(group).lower()
                success = add_group(groupstr, ctx.author.id)
                if success:
                    added.append(groupstr)
                    add_group_alias_db(groupstr, groupstr, ctx.author.id)
                else:
                    already_exists.append(groupstr)
            if already_exists and added:
                exists = ', '.join(already_exists)
                add = ', '.join(added)
                act = f"Added group(s): {add}!"
                await moderation_auditing(self.disclient, ctx.author, act)
                msg = f"Added group(s): {add}!\nSkipped adding duplicates: {exists}!"
                await ctx.send(embed=success_embed(msg))
            elif added and not already_exists:
                msg = f"Added group(s): {', '.join(added)}!"
                await moderation_auditing(self.disclient, ctx.author, msg)
                await ctx.send(embed=success_embed(msg))
            else:
                msg = f"Skipped adding duplicates: {', '.join(already_exists)}!"
                await ctx.send(embed=error_embed(msg))

    @commands.command(aliases=['addgroupalias'])
    @is_mod()
    async def add_group_alias(self, ctx, group, *aliases):
        """Adds an alias to an existing group that can then be used to
        reference the group in other commands. A list of aliases can be
        passed through in one command, but only one group.
        Example: .add_group_alias redvelvet rv
        Example: .add_group_alias <group> <alias1> <alias2>"""
        group = group.lower()
        added_aliases = []
        invalid_aliases = []
        for alias in aliases:
            alias = alias.lower()
            added = add_group_alias_db(group, alias, ctx.author.id)
            if added:
                added_aliases.append(alias)
            else:
                invalid_aliases.append(alias)
        if invalid_aliases and added_aliases:
            exists = ', '.join(invalid_aliases)
            add = ', '.join(added_aliases)
            act = f"Added alias(es): {add} to {group}!"
            await moderation_auditing(self.disclient, ctx.author, act)
            msg = f"Added alias(es): {add} to {group}!\nSkipped adding duplicates: {exists}!"
            await ctx.send(embed=success_embed(msg))
        elif added_aliases and not invalid_aliases:
            msg = f"Added aliases(s): {', '.join(added_aliases)} to {group}!"
            await moderation_auditing(self.disclient, ctx.author, msg)
            await ctx.send(embed=success_embed(msg))
        else:
            msg = f"Skipped adding duplicate alias(es): {', '.join(invalid_aliases)}!"
            await ctx.send(embed=error_embed(msg))

    @commands.command(aliases=['delgroupalias'])
    @is_mod()
    async def delete_group_alias(self, ctx, group, *aliases):
        """Removes an alias from an existing group.
        A list of aliases can be passed through in one command, but only one group.
        Example: .remove_group_alias redvelvet rv
        Example: .remove_group_alias <group> <alias1> <alias2>"""
        group = group.lower()
        removed_aliases = []
        invalid_aliases = []
        for alias in aliases:
            alias = alias.lower()
            removed = remove_group_alias_db(group, alias)
            if removed:
                removed_aliases.append(alias)
            else:
                invalid_aliases.append(alias)
        if invalid_aliases and removed_aliases:
            exists = ', '.join(invalid_aliases)
            rem = ', '.join(removed_aliases)
            act = f"Removed alias(es): {rem} from {group}!"
            await moderation_auditing(self.disclient, ctx.author, act)
            msg = f"Removed alias(es): {rem} from {group}!\nFailed to removed: {exists}!"
            await ctx.send(embed=success_embed(msg))
        elif removed_aliases and not invalid_aliases:
            msg = f"Removed aliases(s): {', '.join(removed_aliases)} from {group}!"
            await moderation_auditing(self.disclient, ctx.author, msg)
            await ctx.send(embed=success_embed(msg))
        else:
            msg = f"Failed to remove alias(es): {', '.join(invalid_aliases)} from {group}!"
            await ctx.send(embed=error_embed(msg))

    @commands.command(aliases=['addidols', 'addidol', 'add_idol'])
    @is_mod()
    async def add_idols(self, ctx, group, *args):
        """Adds an idol to an already existing group"""
        group = group.lower()
        g_id = find_group_id(group)
        if not g_id:
            await ctx.send(embed=error_embed(f'Group {group} does not exist!'))
            return

        if not args:
            await ctx.send(embed=error_embed('No idols provided!'))
        else:
            # rework lists to strings once working
            members = get_members_of_group(group)
            members = [x[0] for x in members]
            members = set(members)
            args = set(args)
            already_exists = members.intersection(args)
            idol_list = args - members
            added = []
            for idol in idol_list:
                idol = str(idol).lower()
                add_member(group, idol, ctx.author.id)
                add_member_alias_db(group, idol, idol, ctx.author.id)
                added.append(idol)
            if already_exists and added:
                exists = ', '.join(already_exists)
                add = ', '.join(added)
                act = f"Added idol(s): {add} to {group}!"
                await moderation_auditing(self.disclient, ctx.author, act)
                msg = f"Added idol(s): {add} to {group}!\nSkipped adding duplicates: {exists}!"
                await ctx.send(embed=success_embed(msg))
            elif added and not already_exists:
                msg = f"Added idol(s): {', '.join(added)} to {group}!"
                await moderation_auditing(self.disclient, ctx.author, msg)
                await ctx.send(embed=success_embed(msg))
            else:
                msg = f"Skipped adding duplicates: {', '.join(already_exists)}!"
                await ctx.send(embed=error_embed(msg))

    @commands.command(aliases=['addidolalias'])
    @is_mod()
    async def add_idol_alias(self, ctx, group, idol, *aliases):
        """Adds an alias to an idol.
        A list of aliases can be passed through in one command, but only one idol.
        Please ensure you use the members name, and not an alias for the second argument.
        Example: .add_idol_alias redvelvet joy j
        Example: .add_idol_alias <group> <idol> <alias1> <alias2>"""
        group = group.lower()
        idol = idol.lower()
        added_aliases = []
        invalid_aliases = []
        for alias in aliases:
            alias = alias.lower()
            added = add_member_alias_db(group, idol, alias, ctx.author.id)
            if added:
                added_aliases.append(alias)
            else:
                invalid_aliases.append(alias)
        if invalid_aliases and added_aliases:
            exists = ', '.join(invalid_aliases)
            rem = ', '.join(added_aliases)
            act = f"Added alias(es): {rem} to {idol}!"
            await moderation_auditing(self.disclient, ctx.author, act)
            msg = f"Added alias(es): {rem} to {group}!\nFailed to add: {exists}!"
            await ctx.send(embed=success_embed(msg))
        elif added_aliases and not invalid_aliases:
            msg = f"Added aliases(s): {', '.join(added_aliases)} to {idol}!"
            await moderation_auditing(self.disclient, ctx.author, msg)
            await ctx.send(embed=success_embed(msg))
        else:
            msg = f"Failed to add alias(es): {', '.join(invalid_aliases)} to {idol}!"
            await ctx.send(embed=error_embed(msg))

    @commands.command(aliases=['delidolalias', 'deleteidolalias'])
    @is_mod()
    async def delete_idol_alias(self, ctx, group, idol, *aliases):
        """Removes an alias from an idol.
        A list of aliases can be passed through in one command, but only one idol.
        Please ensure you use the members name, and not an alias for the second argument.
        Example: .remove_idol_alias redvelvet joy j
        Example: .remove_idol_alias <group> <idol> <alias1> <alias2>"""
        group = group.lower()
        idol = idol.lower()
        removed_aliases = []
        invalid_aliases = []
        for alias in aliases:
            alias = alias.lower()
            removed = remove_member_alias_db(group, idol, alias)
            if removed:
                removed_aliases.append(alias)
            else:
                invalid_aliases.append(alias)
        if invalid_aliases and removed_aliases:
            exists = ', '.join(invalid_aliases)
            rem = ', '.join(removed_aliases)
            act = f"Removed alias(es): {rem} from {idol}!"
            await moderation_auditing(self.disclient, ctx.author, act)
            msg = f"Removed alias(es): {rem} from {group}!\nFailed to removed: {exists}!"
            await ctx.send(embed=success_embed(msg))
        elif removed_aliases and not invalid_aliases:
            msg = f"Removed aliases(s): {', '.join(removed_aliases)} from {idol}!"
            await moderation_auditing(self.disclient, ctx.author, msg)
            await ctx.send(embed=success_embed(msg))
        else:
            msg = f"""Failed to remove alias(es): {', '.join(invalid_aliases)} from {idol}!
                   \nPlease make sure you do not use an alias for the idol name."""
            await ctx.send(embed=error_embed(msg))

    @commands.command(aliases=['removetag', 'removetagfromlink, remove_tag_from_link'])
    @is_mod()
    async def remove_tag(self, ctx, link, *tags):
        """
        Removes tag(s) from a link previously added
        Example: <link> <tag> <tag> <tag>
        Any number of tags can be removed in one command.
        """
        tags_list = tags
        # rework lists to strings once working
        removed = []
        not_there = []
        for tag in tags_list:
            tag = tag.lower()
            remove = remove_tag_from_link(link, tag)
            if remove:
                removed.append(tag)
            else:
                not_there.append(tag)
        if removed and not_there:
            r = ', '.join(removed)
            nt = ', '.join(not_there)
            act = f"Removed tag(s): {r} from {link}"
            await moderation_auditing(self.disclient, ctx.author, act)
            await ctx.send(embed=success_embed(f'Removed {r} tag(s) from link!\nLink did not have: {nt}'))
        elif removed:
            r = ', '.join(removed)
            act = f"Removed tag(s): {r} from the link:\n{link}"
            await moderation_auditing(self.disclient, ctx.author, act)
            await ctx.send(embed=success_embed(f'Removed {r} tag(s) from link!'))
        else:
            nt = ', '.join(not_there)
            await ctx.send(embed=error_embed(f'Link did not have tag(s): {nt}!'))

    @commands.command(aliases=['createtag'])
    @is_mod()
    async def create_tag(self, ctx, tag):
        """Adds a new tag, which will be available for use."""
        if not check_user_is_mod(ctx):
            await ctx.send(embed=permission_denied_embed())
            return

        tag = tag.lower()
        added = add_tag(tag, ctx.author.id)
        add_tag_alias_db(tag, tag, ctx.author.id)
        if added:
            act = f'Added tag: {tag}!'
            await moderation_auditing(self.disclient, ctx.author, act)
            await ctx.send(embed=success_embed(act))
        else:
            await ctx.send(embed=error_embed(f'{tag} already exists!'))

    @commands.command(aliases=['deletetag', 'deltag'])
    @is_mod()
    async def delete_tag(self, ctx, tag):
        """Completely deletes a tag.
        All links with this tag, will no longer have this tag."""
        tag = tag.lower()
        removed = remove_tag(tag)
        if removed:
            act = f'Deleted tag: {tag}!'
            await moderation_auditing(self.disclient, ctx.author, act)
            await ctx.send(embed=success_embed(act))
        else:
            await ctx.send(embed=error_embed(f'{tag} does not exist!'))

    @commands.command(aliases=['addtagalias'])
    @is_mod()
    async def add_tag_alias(self, ctx, tag, *aliases):
        """Adds an alias to a tag.
        A list of aliases can be passed through in one command, but only one tag.
        Please ensure you use the tag name, and not an alias for the first argument.
        Example: .add_tag_alias <tag> <alias>
        Example: .add_tag_alias <tag> <alias1> <alias2>"""
        tag = tag.lower()
        added_aliases = []
        invalid_aliases = []
        for alias in aliases:
            alias = alias.lower()
            added = add_tag_alias_db(tag, alias, ctx.author.id)
            if added:
                added_aliases.append(alias)
            else:
                invalid_aliases.append(alias)
        if invalid_aliases and added_aliases:
            exists = ', '.join(invalid_aliases)
            add = ', '.join(added_aliases)
            act = f"Added alias(es): {add} to {tag}!"
            await moderation_auditing(self.disclient, ctx.author, act)
            msg = f"Added alias(es): {add} to {tag}!\nSkipped adding duplicates: {exists}!"
            await ctx.send(embed=success_embed(msg))
        elif added_aliases and not invalid_aliases:
            msg = f"Added aliases(s): {', '.join(added_aliases)} to {tag}!"
            await moderation_auditing(self.disclient, ctx.author, msg)
            await ctx.send(embed=success_embed(msg))
        else:
            msg = f"Skipped adding duplicate alias(es): {', '.join(invalid_aliases)}!"
            await ctx.send(embed=error_embed(msg))

    @commands.command(aliases=['deltagalias', 'removetagalias', 'dta'])
    @is_mod()
    async def delete_tag_alias(self, ctx, tag, *aliases):
        """Removes an alias from a tag.
        A list of aliases can be passed through in one command, but only one tag.
        Please ensure you use the tag name, and not an alias for the first argument.
        Example: .delete_tag_alias <tag> <alias>
        Example: .delete_tag_alias <tag> <alias1> <alias2>"""
        tag = tag.lower()
        removed_aliases = []
        invalid_aliases = []
        for alias in aliases:
            alias = alias.lower()
            removed = remove_tag_alias_db(tag, alias)
            if removed:
                removed_aliases.append(alias)
            else:
                invalid_aliases.append(alias)
        if invalid_aliases and removed_aliases:
            exists = ', '.join(invalid_aliases)
            rem = ', '.join(removed_aliases)
            act = f"Removed alias(es): {rem} from {tag}!"
            await moderation_auditing(self.disclient, ctx.author, act)
            msg = f"Removed alias(es): {rem} from {tag}!\nFailed to removed: {exists}!"
            await ctx.send(embed=success_embed(msg))
        elif removed_aliases and not invalid_aliases:
            msg = f"Removed aliases(s): {', '.join(removed_aliases)} from {tag}!"
            await moderation_auditing(self.disclient, ctx.author, msg)
            await ctx.send(embed=success_embed(msg))
        else:
            msg = f"Failed to remove alias(es): {', '.join(invalid_aliases)} from {tag}!"
            await ctx.send(embed=error_embed(msg))

    @commands.command(aliases=[
        'delfancam', 'delete_fancam', 'delete_image', 'delimage', 'delete_gfy', 'delgfy', 'del', 'dellink'
    ])
    @is_mod()
    async def delete_link(self, ctx, group, idol, *links):
        """
        Deletes link(s) from an idol.
        Example: .delete_link <group> <idol> <link> <link> <link>
        """
        link_list = links
        group = group.lower()
        idol = idol.lower()
        # change list to string later
        failed = []
        success = []
        for link in link_list:
            if '-' in link:
                link = link.split('-')[0]
            removed = remove_link(group, idol, link)
            if removed:
                success.append(link)
            else:
                failed.append(link)
        if failed and not success:
            f = ', '.join(failed)
            await ctx.send(embed=error_embed(f'Failed to delete: {f}'))
        elif len(success) > 0 and failed:
            f = ', '.join(failed)
            s = '\n' + '\n'.join(success)
            act = f'Deleted link(s) from {group} {idol}: {s}'
            await moderation_auditing(self.disclient, ctx.author, act)
            await ctx.send(embed=success_embed(f'Removed {len(success)} links!\nFailed to delete: {f}'))
        else:
            s = '\n' + '\n'.join(success)
            act = f'Deleted link(s) from {group} {idol}: {s}'
            await moderation_auditing(self.disclient, ctx.author, act)
            await ctx.send(embed=success_embed(f'Removed {len(success)} links!'))

    @commands.command(aliases=['delgroup', 'deletegroup'])
    @is_mod()
    async def delete_group(self, ctx, group):
        """
        Deletes an entire group and all idols within
        Example: .delete_group <group>
        """
        group = group.lower()
        removed = remove_group(group)
        if removed:
            act = f"Deleted group: {group}"
            await moderation_auditing(self.disclient, ctx.author, act)
            await ctx.send(embed=success_embed(f'Removed {group}'))
        else:
            await ctx.send(embed=error_embed(f'No group added called {group}!'))

    @commands.command(aliases=['delidol', 'delidols', 'deleteidol', 'deleteidols'])
    @is_mod()
    async def delete_idols(self, ctx, group, *args):
        """
        Deletes all idol(s) specified in a group
        Example: .delete_idols <group> <idol_1> <idol_2>
        """
        group = group.lower()
        g_id = find_group_id(group)
        if not g_id:
            await ctx.send(embed=error_embed(f'No group added named {group}!'))
            return

        if not args:
            await ctx.send(embed=error_embed('No idols provided!'))
        else:
            members = get_members_of_group(group)
            members = [x[0] for x in members]
            members = set(members)
            args = set(args)
            idol_list = members.intersection(args)
            failed = args - members
            success = []
            for idol in idol_list:
                idol = idol.lower()
                a = remove_member(g_id[0], idol)
                if a:
                    success.append(idol)
            if success and failed:
                s = ', '.join(success)
                f = ', '.join(failed)
                act = f"Deleted {s} from {group}."
                await moderation_auditing(self.disclient, ctx.author, act)
                await ctx.send(embed=success_embed(f'Deleted: {s}!\nFailed to delete {f}!'))
            elif success and not failed:
                s = ', '.join(success)
                act = f"Deleted: {s} from {group}!"
                await moderation_auditing(self.disclient, ctx.author, act)
                await ctx.send(embed=success_embed(act))
            else:
                f = ', '.join(failed)
                await ctx.send(embed=error_embed(f'Failed to delete {f}'))

    @commands.command(aliases=['addauditing'])
    @is_mod()
    async def add_auditing(self, ctx):
        """Adds auditing from this channel, as links are added to
        the bot, they will also be posted here so all new additions
        can be viewed."""
        if not check_user_is_mod(ctx):
            await ctx.send(embed=permission_denied_embed())
            return

        add_channel(ctx.channel.id)
        added = add_auditing_channel(ctx.channel.id)
        if added:
            des = 'Added this channel to the auditing list!'
            await ctx.send(embed=success_embed(des))
        else:
            des = 'Channel already in auditing list!'
            await ctx.send(embed=error_embed(des))

    @commands.command(aliases=['removeauditing'])
    @is_mod()
    async def remove_auditing(self, ctx):
        """Removes auditing from this channel!"""
        removed = remove_auditing_channel(ctx.channel.id)
        if removed:
            des = 'Removed this channel from the auditing list!'
            await ctx.send(embed=success_embed(des))
        else:
            des = 'Channel not in the auditing list!'
            await ctx.send(embed=error_embed(des))

    @commands.command(aliases=['delcommand', 'dc'])
    @is_mod()
    async def delete_command(self, ctx, command):
        """Removes a custom command created previously."""
        command = command.lower()
        removed = remove_command(command)
        if removed:
            act = f"Removed command: {command}"
            await moderation_auditing(self.disclient, ctx.author, act)
            await ctx.send(embed=success_embed(f'Removed {command}!'))
        else:
            await ctx.send(embed=error_embed(f'Command {command} does not exist!'))


async def moderation_auditing(disclient, author, action):
    """Posts moderator actions to the mod auditing channel in the discord."""
    mod_audcha = disclient.get_channel(apis_dict["mod_audit_channel"])
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    s = f'`{dt}`: `{author}`:\n{action}'
    embed = discord.Embed(title=s,
                          color=discord.Color.blurple())
    await mod_audcha.send(embed=embed)


def setup(disclient):
    disclient.add_cog(Moderation(disclient))
    disclient.add_cog(Owner(disclient))
