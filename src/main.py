from typing import Any, List, Optional
from dotenv import load_dotenv
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware


from fastapi import FastAPI
from notion_client import AsyncClient
import os
from enum import Enum

from pydantic import BaseModel

load_dotenv()

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


app = FastAPI()


notion = AsyncClient(auth=os.environ.get("NOTION_TOKEN"))
kanban_database_id = "6ecf686fc65548b683999fd8f7ce5184"


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Status(Enum):
    BACKLOG = "Backlog"
    SPRINT_BACKLOG = "Sprint Backlog"
    DAILY_BACKLOG = "Daily Backlog"
    IN_PROGRESS = "In Progress"
    DONE_SPRINT = "Done Sprint"
    DONE = "Done"


class Tag(Enum):
    FIVE_S = "5S"
    EPIC_1 = "EPIC 1"
    EPIC_2 = "EPIC 2"
    EPIC_3 = "EPIC 3"
    PRIO_1 = "Prio 1"
    PRIO_2 = "Prio 2"
    PRIO_3 = "Prio 3"
    BUG = "Bug"


class KanbanInput(BaseModel):
    status: Optional[List[Status]] = []
    tags: Optional[List[Tag]] = []
    assign_id: Optional[str] = None


@app.post(
    "/kanban",
    openapi_extra={"x-openai-isConsequential": False},
    description="Get tickets from the kanban board. You can filter by status and tags. Status are under an OR condition and tags are under an AND condition.",
)
async def read_kanban(
    kanban_input: KanbanInput,
):
    status = kanban_input.status
    tags = kanban_input.tags
    assign_id = kanban_input.assign_id

    or_status_filters = []
    if status is not None and len(status) > 0:
        for s in status:
            or_status_filters.append(
                {"property": "Status", "status": {"equals": s.value}}
            )

    and_tag_filters = []
    if tags is not None and len(tags) > 0:
        for t in tags:
            and_tag_filters.append(
                {"property": "Tag", "multi_select": {"contains": t.value}}
            )

    filter: Any = None

    if len(and_tag_filters) > 0:
        filter = {"and": and_tag_filters}

    if assign_id is not None:
        if filter is None:
            filter = {
                "and": [{"property": "Assign", "people": {"contains": assign_id}}]
            }
        else:
            filter["and"].append(
                {"property": "Assign", "people": {"contains": assign_id}}
            )

    if len(and_tag_filters) == 0:
        if filter is None:
            filter = {"or": or_status_filters}
        elif filter["and"]:
            filter["and"].append({"or": or_status_filters})

    print("filter", filter)

    try:
        if filter is None:
            response = await notion.databases.query(database_id=kanban_database_id)
        else:
            response = await notion.databases.query(
                database_id=kanban_database_id, filter=filter
            )

    except Exception as e:
        return "An error occured while fetching the data : {}".format(e)

    pages_titles = list(
        map(
            notion_page_to_dto,
            response["results"],
        )
    )
    return pages_titles


def notion_page_to_dto(page):
    assigned_to = None
    if len(page["properties"]["Assign"]["people"]) > 0:
        assigned_to = page["properties"]["Assign"]["people"][0]["id"]

    return {
        "id": page["id"],
        "name": page["properties"]["Name"]["title"][0]["text"]["content"],
        "status": page["properties"]["Status"]["status"]["name"],
        "tags": list(
            map(lambda x: x["name"], page["properties"]["Tag"]["multi_select"])
        ),
        "assignedTo": assigned_to,
    }


app.openapi_schema = get_openapi(
    title="Notion Kanban Board API by Matthieu Bezard",
    version="1.0",
    routes=app.routes,
    servers=[
        {"url": "https://7f16-2a01-e0a-e2-af00-85ad-c24f-33ec-f952.ngrok-free.app"},
    ],
)
