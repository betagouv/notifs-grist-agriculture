from grist import api
import send_email


def update():
    accessResponse = api.call("access")
    accesses = accessResponse.json()

    viewersAccessToRemove = {
        person["email"]: None
        for person in accesses["users"]
        if (person["access"] or person["parentAccess"]) == "viewers"
    }
    editorAccesses = [
        person["email"] for person in accesses["users"] if person["access"] != "viewers"
    ]

    people = [person for person in api.fetch_table("Personnes") if len(person.Email)]
    toAdd = [p.Email for p in people if p.Email not in editorAccesses]

    peopleEmails = [p.Email for p in people]
    toRemove = [ea for ea in editorAccesses if ea not in peopleEmails]

    updatesToDo = {
        **viewersAccessToRemove,
        **{email: None for email in toRemove},
        **{email: "editors" for email in toAdd},
    }
    if len(updatesToDo):
        data = {"delta": {"maxInheritedRole": "owners", "users": updatesToDo}}
        api.call("access", data, "PATCH")
        notify(updatesToDo)


def notify(updatesToDo):
    names = {None: "Suppression :", "editors": "Édition :"}

    newAccessMap = {}
    for email in updatesToDo:
        access = updatesToDo[email]
        if access not in newAccessMap:
            newAccessMap[access] = []
        newAccessMap[access].append(email)
    newAccessMap
    body = "\n\n".join(
        [
            "\n".join([names[a], *[f"- {e}" for e in newAccessMap[a]]])
            for a in newAccessMap
        ]
    )
    send_email.send("[Grist] Mise à jour des droits d'accès", body)
