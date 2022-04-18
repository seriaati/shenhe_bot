# 帳號class
class User:
    def __init__(self, discordID, uid, ltuid, ltoken, username, dm, count):
        self.discordID = discordID
        self.uid = uid
        self.ltuid = ltuid
        self.ltoken = ltoken
        self.username = username
        self.dm = dm
        self.count = count

# 小組class
class Group:
    def __init__(self, name):
        members = []
        self.name = name
        self.members = members

# 角色
class Character:
    def __init__(self, name, level, constellation, iconUrl, friendship, weapon, refinement, weaponLevel, artifacts, artifactIcons):
        self.name = name 
        self.level = level
        self.constellation = constellation
        self.iconUrl = iconUrl
        self.friendship = friendship
        self.weapon = weapon
        self.refinement = refinement
        self.weaponLevel = weaponLevel
        self.artifacts = artifacts
        self.artifactIcons = artifactIcons