import socketio
from quart import Blueprint, request, jsonify
import utils
from objects import glob
from objects.beatmap import Beatmap
from objects.room import (
    Room,
    PlayerMulti,
    PlayerStatus,
    RoomStatus,
    WinCondition,
    PlayerTeam,
    Match,
)

bp = Blueprint("multi", __name__)
bp.prefix = "/multi/"
sio = socketio.AsyncServer(
    async_mode="asgi", cors_allowed_origins="*", engineio_logger=True
)


class MultiNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace):
        super().__init__(namespace)

    @property
    def room_id(self):
        return self.namespace.split("/")[-1]

    async def on_disconnect(self, sid, environ, *args):
        print(f"Client disconnected: {sid}")
        room_info = glob.rooms.get(self.room_id)

        disconnected_player = None
        for player in room_info.players:
            if player.sid == sid:
                disconnected_player = player
                break

        await sio.emit(
            "playerLeft", data=str(disconnected_player.uid), namespace=self.namespace
        )

        # Check if the disconnected player was the host
        if room_info.host.uid == disconnected_player.uid:
            # Assign a new host
            for new_host in room_info.players:
                if new_host.uid != disconnected_player.uid:
                    room_info.host = new_host
                    await sio.emit(
                        event="hostChanged",
                        data=str(room_info.host.uid),
                        namespace=self.namespace,
                    )
                    break

        # Remove the player from the room
        for i in range(len(room_info.players)):
            if room_info.players[i] == disconnected_player:
                room_info.players.pop(i)
                break

        if len(room_info.players) == 0:
            glob.rooms.pop(self.room_id)

    async def on_connect(self, sid, environ, *args):
        print(f"Client connected: {sid}")
        room_info = glob.rooms.get(self.room_id)
        if room_info.isLocked == True:
            if args[0]["password"] != room_info.password:
                await sio.emit(
                    "error", "Wrong password", namespace=self.namespace, to=sid
                )
                await sio.disconnect(sid=sid, namespace=self.namespace)
        room_info.players.append(PlayerMulti().player(id=args[0]["uid"], sid=sid))

        resp = {
            "id": room_info.id,
            "name": room_info.name,
            "beatmap": {
                "md5": room_info.map.md5,
                "title": room_info.map.title,
                "artist": room_info.map.artist,
                "version": room_info.map.version,
                "creator": room_info.map.creator,
                "beatmapSetId": room_info.map.set_id,
            },
            "host": room_info.host.as_json(),
            "isLocked": room_info.isLocked,
            "gameplaySettings": room_info.gameplaySettings.as_json(),
            "maxPlayers": room_info.maxPlayers,
            "mods": room_info.mods.as_json(),
            "players": [p.as_json() for p in room_info.players],
            "status": room_info.status,
            "teamMode": room_info.teamMode,
            "winCondition": room_info.winCondition,
            "sessionId": utils.make_uuid(),
        }
        # Emit initial connection event
        await sio.emit(
            data=resp, namespace=self.namespace, event="initialConnection", to=sid
        )

        # If there is only one player in the room, return early
        if len(room_info.players) == 1:
            return

        # Find the new player who just joined
        new_player = None
        for player in room_info.players:
            if player.sid == sid:
                new_player = player
                break

        # Notify other players about the new player joining
        for player in room_info.players:
            if player.sid != sid:
                await sio.emit(
                    "playerJoined",
                    data=new_player.as_json(),
                    namespace=self.namespace,
                    to=player.sid,
                )

    async def on_playerModsChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.players:
            if player.sid == sid:
                mods = player.mods
                mods_data = args[0]
                mods.mods = mods_data["mods"]
                mods.speedMultiplier = mods_data["speedMultiplier"]
                mods.flFollowDelay = mods_data["flFollowDelay"]
                mods.customAR = mods_data.get("customAR", 0)
                mods.customOD = mods_data.get("customOD", 0)
                mods.customCS = mods_data.get("customCS", 0)
                mods.customHP = mods_data.get("customHP", 0)

                await sio.emit(
                    "playerModsChanged",
                    (str(player.uid), mods_data),
                    namespace=self.namespace,
                )
                break

    async def on_playerStatusChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.players:
            if player.sid == sid:
                if args[0] == 0:
                    player.status = PlayerStatus.IDLE
                    if (
                        room_info.status == RoomStatus.PLAYING
                        and player.status != PlayerStatus.IDLE
                    ):
                        room_info.match.live_score_data[player.uid] = {
                            "score": 0,
                            "combo": 0,
                            "accuracy": 0,
                            "isAlive": False,
                        }
                        room_info.match.submitted_scores[player.uid] = {
                            "score": 0,
                            "combo": 0,
                            "accuracy": 0,
                            "isAlive": False,
                        }
                        print(room_info.match.players)
                        room_info.match.players.remove(player)
                        print(room_info.match.players)
                    if len(room_info.match.players) == 0:
                        room_info.status = RoomStatus.IDLE
                        await sio.emit(
                            "roomStatusChanged",
                            int(room_info.status),
                            namespace=self.namespace,
                        )
                        room_info.match = Match()
                if args[0] == 1:
                    player.status = PlayerStatus.READY
                if args[0] == 2:
                    player.status = PlayerStatus.NOMAP
                if args[0] == 3:
                    player.status = PlayerStatus.PLAYING
                await sio.emit(
                    "playerStatusChanged",
                    (str(player.uid), int(player.status)),
                    namespace=self.namespace,
                )
                break

    async def on_hostChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        room_info.host = PlayerMulti().player(int(args[0]), sid=sid)
        await sio.emit(
            event="hostChanged", data=str(room_info.host.uid), namespace=self.namespace
        )

    async def on_roomModsChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        mods_data = args[0]
        mods = room_info.mods

        mods.mods = mods_data["mods"]
        mods.speedMultiplier = mods_data["speedMultiplier"]
        mods.flFollowDelay = mods_data["flFollowDelay"]
        mods.customAR = mods_data.get("customAR", 0)
        mods.customOD = mods_data.get("customOD", 0)
        mods.customCS = mods_data.get("customCS", 0)
        mods.customHP = mods_data.get("customHP", 0)

        await sio.emit("roomModsChanged", mods_data, namespace=self.namespace)

    async def on_roomGameplaySettingsChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        gameplay_settings = room_info.gameplaySettings
        settings_data = args[0]

        gameplay_settings.isRemoveSliderLock = settings_data.get(
            "isRemoveSliderLock", gameplay_settings.isRemoveSliderLock
        )
        gameplay_settings.isFreeMod = settings_data.get(
            "isFreeMod", gameplay_settings.isFreeMod
        )
        gameplay_settings.allowForceDifficultyStatistics = settings_data.get(
            "allowForceDifficultyStatistics",
            gameplay_settings.allowForceDifficultyStatistics,
        )

        await sio.emit(
            "roomGameplaySettingsChanged",
            gameplay_settings.as_json(),
            namespace=self.namespace,
        )

    async def on_chatMessage(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.players:
            if player.sid == sid:
                await sio.emit(
                    "chatMessage",
                    data=(str(player.uid), args[0]),
                    namespace=self.namespace,
                )

    async def on_roomNameChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        room_info.name = args[0]
        await sio.emit(
            "roomNameChanged", data=str(room_info.name), namespace=self.namespace
        )

    async def on_roomPasswordChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        new_password = args[0]

        if new_password == "":
            room_info.isLocked = False
            room_info.password = ""
        else:
            room_info.isLocked = True
            room_info.password = new_password

    async def on_winConditionChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        if args[0] == 0:
            room_info.winCondition = WinCondition.SCOREV1
        if args[0] == 1:
            room_info.winCondition = WinCondition.ACC
        if args[0] == 2:
            room_info.winCondition = WinCondition.COMBO
        if args[0] == 3:
            room_info.winCondition = WinCondition.SCOREV2

        await sio.emit(
            "winConditionChanged", data=room_info.winCondition, namespace=self.namespace
        )

    async def on_teamModeChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        room_info.teamMode = args[0]
        await sio.emit("teamModeChanged", room_info.teamMode, namespace=self.namespace)
        for player in room_info.players:
            player.team = None
            await sio.emit(
                "playerStatusChanged",
                (str(player.uid), int(PlayerStatus.IDLE)),
                namespace=self.namespace,
            )
            await sio.emit(
                "teamChanged",
                data=(str(player.uid), player.team),
                namespace=self.namespace,
            )

    async def on_teamChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.players:
            if player.sid == sid:
                if args[0] == 0:
                    player.team = PlayerTeam.RED
                if args[0] == 1:
                    player.team = PlayerTeam.BLUE
                await sio.emit(
                    "teamChanged",
                    data=(str(player.uid), player.team),
                    namespace=self.namespace,
                )

    async def on_beatmapChanged(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        if args[0] == {}:
            room_info.status = RoomStatus.CHANGING_BEATMAP
            await sio.emit("beatmapChanged", data=args[0], namespace=self.namespace)
        if args[0] != {}:
            room_info.status = RoomStatus.IDLE
            try:
                room_info.map = await Beatmap.from_md5(args[0]["md5"])
                room_info.map.md5 = args[0]["md5"]
            except:
                room_info.map = Beatmap()
                room_info.map.title = args[0].get("title", "")
                room_info.map.artist = args[0].get("artist", "")
                room_info.map.version = args[0].get("version", "")
                room_info.map.creator = args[0].get("creator", "")
                room_info.map.md5 = args[0].get("md5", "")

            return_data = {}
            return_data["md5"] = room_info.map.md5
            return_data["title"] = room_info.map.title
            return_data["artist"] = room_info.map.artist
            return_data["version"] = room_info.map.version
            return_data["creator"] = room_info.map.creator
            try:
                return_data["beatmapSetId"] = room_info.map.set_id
            except:
                pass

            await sio.emit("beatmapChanged", data=return_data, namespace=self.namespace)

    async def on_playBeatmap(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        room_info.status = RoomStatus.PLAYING
        await sio.emit(
            "roomStatusChanged", data=room_info.status, namespace=self.namespace
        )
        await sio.emit("playBeatmap", namespace=self.namespace)
        for player in room_info.players:
            await sio.emit(
                "playerStatusChanged",
                (str(player.uid), int(PlayerStatus.PLAYING)),
                namespace=self.namespace,
            )
            room_info.match.players.append(player)

    async def on_beatmapLoadComplete(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.match.players:
            if player.sid == sid:
                room_info.match.beatmap_load_status[player.uid] = {"loaded": True}
        if len(room_info.match.beatmap_load_status) == len(room_info.match.players):
            await sio.emit("allPlayersBeatmapLoadComplete", namespace=self.namespace)

    async def on_skipRequested(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)

        for player in room_info.match.players:
            if player.sid == sid:
                room_info.match.skip_requests[player.uid] = {"skipped": True}

        if len(room_info.match.skip_requests) == len(room_info.match.players):
            await sio.emit("allPlayersSkipRequested", namespace=self.namespace)

    async def on_liveScoreData(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        live_score_data = []

        for player in room_info.players:
            if player.sid == sid:
                room_info.match.live_score_data[player.uid] = args[0]

            if len(room_info.match.live_score_data) == len(room_info.match.players):
                live_score_data.append(
                    {
                        "username": player.username,
                        "score": room_info.match.live_score_data[player.uid]["score"],
                        "combo": room_info.match.live_score_data[player.uid]["combo"],
                        "accuracy": room_info.match.live_score_data[player.uid][
                            "accuracy"
                        ],
                        "isAlive": room_info.match.live_score_data[player.uid][
                            "isAlive"
                        ],
                    }
                )

            if room_info.winCondition == WinCondition.SCOREV1:
                live_score_data = sorted(
                    live_score_data, key=lambda x: x["score"], reverse=True
                )
            elif room_info.winCondition == WinCondition.ACC:
                live_score_data = sorted(
                    live_score_data, key=lambda x: x["accuracy"], reverse=True
                )
            elif room_info.winCondition == WinCondition.COMBO:
                live_score_data = sorted(
                    live_score_data, key=lambda x: x["combo"], reverse=True
                )
            elif room_info.winCondition == WinCondition.SCOREV2:
                live_score_data = sorted(
                    live_score_data, key=lambda x: x["score"], reverse=True
                )

        await sio.emit("liveScoreData", live_score_data, namespace=self.namespace)

    async def on_scoreSubmission(self, sid, *args):
        room_info = glob.rooms.get(self.room_id)
        for player in room_info.match.players:
            if player.sid == sid:
                room_info.match.submitted_scores[player.uid] = args[0]

        if len(room_info.match.submitted_scores) == len(room_info.match.players):
            data = []
            for player in room_info.match.players:
                try:
                    data.append(room_info.match.submitted_scores[player.uid])
                except:
                    pass

            if room_info.winCondition == WinCondition.SCOREV1:
                data = sorted(data, key=lambda x: x["score"], reverse=True)
            elif room_info.winCondition == WinCondition.ACC:
                data = sorted(data, key=lambda x: x["accuracy"], reverse=True)
            elif room_info.winCondition == WinCondition.COMBO:
                data = sorted(data, key=lambda x: x["combo"], reverse=True)
            elif room_info.winCondition == WinCondition.SCOREV2:
                data = sorted(data, key=lambda x: x["score"], reverse=True)

            await sio.emit(
                "allPlayersScoreSubmitted", data=data, namespace=self.namespace
            )

            room_info.status = RoomStatus.IDLE
            await sio.emit(
                "roomStatusChanged", int(room_info.status), namespace=self.namespace
            )

            for player in room_info.players:
                player.status = PlayerStatus.IDLE
                await sio.emit(
                    "playerStatusChanged", (str(player.uid), int(player.status))
                )

            room_info.match = Match()

    async def on_playerKicked(self, sid, *args):
        await sio.emit("playerKicked", data=str(args[0]), namespace=self.namespace)


@bp.route("/createroom", methods=["POST"])
async def create_room():
    data = await request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    room_id = str(len(glob.rooms) + 1)  # Simple dynamic ID generation
    room = Room()
    room.id = room_id
    room.name = data["name"]
    room.maxPlayers = data["maxPlayers"]
    room.host = PlayerMulti().player(int(data["host"]["uid"]), sid="")
    try:
        room.map = await Beatmap.from_md5(data["beatmap"]["md5"])
        room.map.md5 = data["beatmap"]["md5"]

    except:
        beatmap = data.get("beatmap", {})
        room.map = Beatmap()
        room.map.title = beatmap.get("title", "")
        room.map.artist = beatmap.get("artist", "")
        room.map.version = beatmap.get("version", "")
        room.map.creator = beatmap.get("creator", "")
        room.map.md5 = ""
    if "password" in data:
        room.password = data["password"]
        room.isLocked = True
    glob.rooms[room_id] = room

    response = {"id": room.id}
    sio.register_namespace(MultiNamespace(f"/multi/{room.id}"))
    return f"{response}"


@bp.route("/getrooms")
async def get_rooms():
    room = []
    for room_id, room_info in glob.rooms.items():
        players = ""
        for player in room_info.players:
            players = ",".join(player.username)
        room.append(
            {
                "id": room_info.id,
                "name": room_info.name,
                "isLocked": room_info.isLocked,
                "gameplaySettings": room_info.gameplaySettings.as_json(),
                "maxPlayers": room_info.maxPlayers,
                "mods": room_info.mods.as_json(),
                "playerNames": players,
                "playerCount": len(room_info.players),
                "status": room_info.status,
                "teamMode": room_info.teamMode,
                "winCondition": room_info.winCondition,
            }
        )

    return jsonify(room)
