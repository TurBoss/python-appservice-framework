import aiohttp

from .async_matrix_api import AsyncHTTPAPI


class AppService:
    """
    Run the Matrix Appservice.

    This needs to maintain state of matrix rooms and bridged users in those rooms.
    """

    def __init__(self, *, matrix_server, server_domain, access_token,
                 user_namespace, room_namespace, loop=None):

        self.client_session = aiohttp.ClientSession(loop=self.loop)
        self.api = AsyncHTTPAPI(matrix_server, self.client_session, access_token)

        self.access_token = access_token
        self.server_name = server_domain
        self.user_namespace = user_namespace
        self.room_namespace = room_namespace

        # Setup web server to listen for appservice calls
        self.app = aiohttp.web.Application(loop=self.loop)
        self._routes()

        self.matrix_events = {}

    ######################################################################################
    # Appservice Web Server Handles
    ######################################################################################

    def _routes(self):
        """
        Add route handlers to the web server.
        """
        self.app.router.add_route('PUT', "/transactions/{transaction}",
                                  self.recieve_matrix_transaction)
        self.app.router.add_route('GET', "/rooms/{alias}", self.room_alias)
        self.app.router.add_route('GET', "/users/{userid}", self.query_userid)

    async def recieve_matrix_transaction(self, request):
        """
        Receive an Appservice push matrix event.
        """
        return aiohttp.web.Response(status=404)

    async def room_alias(self, request):
        """
        Handle an Appservice room_alias call.
        """
        return aiohttp.web.Response(status=404)

    async def query_userid(self, request):
        """
        Handle an Appservice userid call.
        """
        return aiohttp.web.Response(status=404)

    ######################################################################################
    # Matrix Event Decorators
    ######################################################################################

    def matrix_recieve_message(self, coro):
        """
        coro(appservice, event)
        """
        self.matrix_events['recieve_message'] = coro

        return coro

    def matrix_user_join(self, coro):
        """
        coro(appservice, event)
        """
        self.matrix_events['user_join'] = coro

        return coro

    def matrix_user_part(self, coro):
        """
        coro(appservice, event)
        """
        self.matrix_events['user_part'] = coro

        return coro

    def matrix_user_typing(self, coro):
        """
        coro(appservice, event)
        """
        self.matrix_events['user_typing'] = coro

        return coro

    # TODO: Add matrix user read

    ######################################################################################
    # Service Event Decorators
    ######################################################################################

    def service_room_exists(self, coro):
        """
        Decorator to query if a matrix room alias exists.

        coro(appservice, matrix_room_alias)
        """
        self.service_events['room_exists'] = coro

        return coro

    def service_join_room(self, coro):
        """
        Decorator for when a service user joins a room.

        coro(appservice)

        Returns:
            matrix_mxid : `str`
            matrix_room_alias : `str`
        """

        async def join_room(self):
            mxid, room_alias = await coro(self)

            # TODO: Perform matrix side stuff

        self.service_events['join_room'] = join_room

        return join_room

    def service_part_room(self, coro):
        """
        Decorator for when a service user leaves a room.

        coro(appservice)

        Returns:
            matrix_mxid : `str`
            matrix_room_alias : `str`
        """
        async def part_room(self):
            mxid, room_alias = await coro(self)

            # TODO: Perform matrix side stuff

        self.service_events['part_room'] = part_room

        return part_room

    def service_change_profile_image(self, coro):
        """
        coro(appservice)

        Returns:
            mxid
            image_url
            force_update
        """

        async def profile_image(self):
            user_id, image_url, force = await coro(self)

            resp = await self.set_matrix_profile_image(user_id, image_url, force)

            return resp

        self.service_events['profile_image'] = profile_image

        return profile_image

    ######################################################################################
    # Appservice Methods
    ######################################################################################

    async def add_appservice_user(self, username):
        pass

    async def join_user_room(self, username, room):
        pass

    async def set_matrix_profile_image(self, user_id, image_url, force=False):
        if force or not await self.matrix_client.get_avatar_url(user_id) and image_url:
            # Download profile picture
            async with self.client_session.request("GET", image_url) as resp:
                data = await resp.read()

            # Upload to homeserver
            resp = await self.matrix_client.media_upload(data, resp.content_type,
                                                            user_id=user_id)
            json = await resp.json()
            avatar_url = json['content_uri']

            # Set profile picture
            resp = await self.matrix_client.set_avatar_url(user_id, avatar_url)

            return resp
