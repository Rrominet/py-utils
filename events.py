import os
import json
import time as t
import random
import datetime

events_root_dir = "/opt/events/data"

NOW = 0
TODAY = 1
THIS_WEEK = 2
THIS_MONTH = 3
CHECK_IF_TIME = 4
URGENT = NOW

def write(name, parent="", time=-1, description="", data=None,
          changes_keys=None, changes_conditions=None,
          urgency=CHECK_IF_TIME):
    if data is None:
        data = {}

    if changes_keys is None:
        changes_keys = []

    if changes_conditions is None:
        changes_conditions = []

    try:
        root = os.path.join(events_root_dir, "events")
        os.makedirs(root, exist_ok=True)
    except Exception as error:
        return {"success": False, "message": str(error)}

    if time == -1:
        event_time = int(t.time())
    else:
        event_time = time

    event = {
        "id": str(event_time) + "_" + str(random.randint(10000, 99999)),
        "name": name,
        "parent": parent,
        "time": event_time,
        "description": description,
        "data": data,
        "urgency": urgency
    }

    parent_dir = os.path.join(root, str(parent))
    date_dir = os.path.join(
        parent_dir,
        datetime.datetime.fromtimestamp(event_time).strftime("%Y-%m-%d")
    )

    previous_events = []
    if os.path.isdir(parent_dir):
        for current_root, dirs, files in os.walk(parent_dir):
            for file_name in files:
                try:
                    with open(os.path.join(current_root, file_name), "r") as file:
                        previous_events.append(json.load(file))
                except Exception:
                    pass

    for previous_event in previous_events:
        matches = True

        for key in changes_keys:
            if key in event:
                current_value = event.get(key)
                previous_value = previous_event.get(key)
            else:
                current_value = event.get("data", {}).get(key)
                previous_value = previous_event.get("data", {}).get(key)

            if current_value != previous_value:
                matches = False
                break

        if matches and changes_keys:
            return {"success": True, "message": ""}

        for condition in changes_conditions:
            if condition(previous_event, event):
                return {"success": True, "message": ""}

    try:
        os.makedirs(date_dir, exist_ok=True)
        with open(os.path.join(date_dir, event["id"]), "w") as file:
            json.dump(event, file)
    except Exception as error:
        return {"success": False, "message": str(error)}

    return {"success": True, "message": ""}


def read(parent=None, name=None, time_range=None, key_match=None,
         urgency=None, include_consumed=False):
    if time_range is None:
        time_range = [-1, -1]

    if key_match is None:
        key_match = []

    result = []
    root = os.path.join(events_root_dir, "events")

    if not os.path.isdir(root):
        return {"success": True, "message": "", "data": result}

    try:
        for current_root, dirs, files in os.walk(root):
            for file_name in files:
                try:
                    with open(os.path.join(current_root, file_name), "r") as file:
                        event = json.load(file)
                except Exception:
                    continue

                if parent is not None and event.get("parent", "") != parent:
                    continue

                if name is not None and event.get("name") != name:
                    continue

                if time_range[0] != -1 and event.get("time", -1) < time_range[0]:
                    continue

                if time_range[1] != -1 and event.get("time", -1) > time_range[1]:
                    continue

                if urgency is not None and event.get("urgency") != urgency:
                    continue

                if not include_consumed and event.get("consumed", False):
                    continue

                matches = True
                for item in key_match:
                    key = item.get("key")
                    value = item.get("value")

                    if key in event:
                        event_value = event.get(key)
                    else:
                        event_value = event.get("data", {}).get(key)

                    if event_value != value:
                        matches = False
                        break

                if matches:
                    if not "consumed" in event: 
                        event["consumed"] = False
                    result.append(event)
    except Exception as error:
        return {"success": False, "message": str(error), "data": []}

    return {"success": True, "message": "", "data": result}


def consume(id):
    root = os.path.join(events_root_dir, "events")

    if not os.path.isdir(root):
        return {"success": False, "message": "Event not found"}

    try:
        for current_root, dirs, files in os.walk(root):
            for file_name in files:
                file_path = os.path.join(current_root, file_name)

                try:
                    with open(file_path, "r") as file:
                        event = json.load(file)
                except Exception:
                    continue

                if event.get("id") != id:
                    continue

                event["consumed"] = True

                with open(file_path, "w") as file:
                    json.dump(event, file)

                return {"success": True, "message": ""}

    except Exception as error:
        return {"success": False, "message": str(error)}

    return {"success": False, "message": "Event not found"}

def consumeFromParent(parent):
    result = read(parent=parent)

    if not result.get("success"):
        return result

    for event in result.get("data", []):
        consumed = consume(event.get("id"))
        if not consumed.get("success"):
            return consumed

    return {"success": True, "message": ""}


def consumeFromName(name):
    result = read(name=name)

    if not result.get("success"):
        return result

    for event in result.get("data", []):
        consumed = consume(event.get("id"))
        if not consumed.get("success"):
            return consumed

    return {"success": True, "message": ""}


def consumeFromTimeRange(start, end):
    result = read(time_range=[start, end])

    if not result.get("success"):
        return result

    for event in result.get("data", []):
        consumed = consume(event.get("id"))
        if not consumed.get("success"):
            return consumed

    return {"success": True, "message": ""}


def consumeFromKeyMatch(key_match):
    result = read(key_match=key_match)

    if not result.get("success"):
        return result

    for event in result.get("data", []):
        consumed = consume(event.get("id"))
        if not consumed.get("success"):
            return consumed

    return {"success": True, "message": ""}


def consumeFromUrgency(urgency):
    result = read(urgency=urgency)

    if not result.get("success"):
        return result

    for event in result.get("data", []):
        consumed = consume(event.get("id"))
        if not consumed.get("success"):
            return consumed

    return {"success": True, "message": ""}
