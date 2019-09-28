import requests
import random
from dictor import dictor


def login(email, password):
    s = requests.Session()
    login = s.post('https://api.tonie.cloud/v2/sessions', json={"email": email, "password": password})
    login.raise_for_status()
    s.headers.update({'Authorization': 'Bearer ' + login.json()["jwt"]})
    return s


def get_creative_tonies(session):
    data = {
        "query": "\n  {\n    me {\n      email\n      isVerified\n      requiresVerificationToUpload\n    }\n    households {\n      access\n      canLeave\n      foreignCreativeTonieContent\n      id\n      image\n      name\n      creativeTonies {\n        id\n        name\n        live\n        imageUrl\n        secondsRemaining\n      }\n      memberships {\n        id\n        isSelf\n      }\n    }\n  }\n"}
    content = session.post("https://api.tonie.cloud/v2/graphql", json=data)
    content.raise_for_status()
    return content.json()


def get_tonie_chapters(session, householdId, creativeTonieId):
    data = {
        "query": "\n  query ($householdId: String, $creativeTonieId: String){\n    me {\n      email\n      isVerified\n      requiresVerificationToUpload\n    }\n    config {\n      maxChapters\n      maxSeconds\n      maxBytes\n      accepts\n    }\n    households(id: $householdId) {\n      id\n      access\n      image\n      name\n      creativeTonies(id: $creativeTonieId) {\n        id\n        name\n        live\n        private\n        imageUrl\n        transcoding\n        secondsRemaining\n        secondsPresent\n        chaptersPresent\n        chaptersRemaining\n        chapters {\n          id\n          title\n          file\n          seconds\n          transcoding\n        }\n        permissions {\n          membershipId\n          displayName\n          profileImage\n          permission\n        }\n      }\n    }\n  }\n",
        "variables": {"householdId": householdId, "creativeTonieId": creativeTonieId},
        "cancelToken": {"promise": {}}}
    content = session.post("https://api.tonie.cloud/v2/graphql", json=data)
    content.raise_for_status()
    #    pprint(content.json())
    return dictor(content.json(), "data.households.0.creativeTonies.0.chapters")


def reorder_songs(session, householdId, creativeTonieId, chapters):
    random.shuffle(chapters)
    data = {"chapters": chapters}
    content = session.patch(f"https://api.tonie.cloud/v2/households/{householdId}/creativetonies/{creativeTonieId}",
                            json=data)
    content.raise_for_status()
    print("Done")


if __name__ == "__main__":
    import configparser

    config = configparser.ConfigParser()
    config.read('tonie.ini')

    email = config.get("DEFAULT", "email")
    password = config.get("DEFAULT", "password")
    reorder_songs_for_tonies = ["Lern", "Mut", "Schlaf", "Spiel"]
    # reorder_songs_for_tonies = ["Mut"]

    print("Creative tonies")
    session = login(email, password)
    creative_tonies = get_creative_tonies(session)
    # only first household is supported
    household = dictor(creative_tonies, "data.households.0")
    print("Household: %s - %s" % (household["id"], household["name"]))
    for item in dictor(creative_tonies, "data.households.0.creativeTonies"):
        print("%s - %s" % (item["id"], item["name"]))
        chapters = get_tonie_chapters(session, household["id"], item["id"])
        #    for chapter in chapters:
        #        print(chapter)

        if reorder_songs_for_tonies == "all" or item["name"] in reorder_songs_for_tonies:
            print("Reorder song for tonie %s " % (item["name"]))
            reorder_songs(session, household["id"], item["id"], chapters)
